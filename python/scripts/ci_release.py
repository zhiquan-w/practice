#!/usr/bin/env python3

"""
from https://gitlab.com/gitlab-automation-toolkit/gitlab-auto-release/-/blob/master/src/gitlab_auto_release/cli.py
from https://gitlab.com/alelec/gitlab-release/-/raw/master/gitlab_release.py
"""

import os
import io
import re
import json
import codecs
import zipfile
import argparse
import itertools
import mimetypes
import urllib.error
from glob import glob
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit, urlencode, quote
import requests


class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        # self.boundary = mimetools.choose_boundary()
        self.boundary = "----------lImIt_of_THE_fIle_eW_$"
        return

    def get_content_type(self):
        return "multipart/form-data; boundary=%s" % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        self.files.append((fieldname, filename, mimetype, body))
        return

    def get_binary(self):
        """Return a binary buffer containing the form data, including attached files."""

        def to_bytes(s):
            return s.encode("ascii") if isinstance(s, str) else s

        part_boundary = "--" + self.boundary

        binary = io.BytesIO()
        needsCLRF = False
        # Add the form fields
        for name, value in self.form_fields:
            if needsCLRF:
                binary.write("\r\n")
            needsCLRF = True

            block = [part_boundary, 'Content-Disposition: form-data; name="%s"' % name, "", value]
            binary.write("\r\n".join(block))

        # Add the files to upload
        for field_name, filename, content_type, body in self.files:
            if needsCLRF:
                binary.write("\r\n")
            needsCLRF = True

            block = [
                part_boundary,
                str('Content-Disposition: file; name="%s"; filename="%s"' % (field_name, filename)),
                "Content-Type: %s" % content_type,
                "",
            ]
            binary.write(b"\r\n".join([to_bytes(s) for s in block]))
            binary.write(b"\r\n")
            binary.write(to_bytes(body))

        # add closing boundary marker,
        binary.write(to_bytes("\r\n--" + self.boundary + "--\r\n"))
        return binary


def url_server_path(url):
    scheme, netloc, path, query, fragment = urlsplit(url)
    return f"{scheme}{netloc}", f"{path}{query}{fragment}"


def try_to_get_changelog(changelog, tag_name):
    """Try to get details from the changelog to include in the description of the release.

    Args:
        changelog (str): Path to changelog file.
        tag_name (str): The tag name i.e. release/0.1.0, must contain semantic versioning somewhere in the tag (0.1.0).

    Returns
        str: The description to use for the release.

    """
    try:
        description = f"\n\n{get_changelog(changelog, tag_name)}"
    except (IndexError, AttributeError):
        raise SystemExit(f"Invalid tag name doesn't contain a valid semantic version {tag_name}.")
    except FileNotFoundError:
        raise SystemExit(f"Unable to find changelog file at {changelog}.")
    except OSError:
        raise SystemExit(f"Unable to open changelog file at {changelog}.")

    return description


def get_changelog(changelog, tag_name):
    """Gets details from the changelog to include in the description of the release.
    The changelog must adhere to the keepachangelog format.

    Args:
        changelog (str): Path to changelog file.
        tag_name (str): The tag name i.e. release/0.1.0, must contain semantic versioning somewhere in the tag (0.1.0).

    Returns
        str: The description to use for the release.

    Raises:
        AttributeError: If the tag_name doesn't contain semantic versioning somewhere within the name.
        FileNotFoundError: If the file couldn't be found.
        OSError: If couldn't open file for some reason.

    """
    with open(changelog, "r") as change:
        content = change.read()
        semver = r"((([0-9]+)\.([0-9]+)\.([0-9]+)(?:-([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"
        semver_tag = re.search(semver, tag_name).group(0)
        if semver_tag:
            semver_changelog = f"## [v{semver_tag}]"
            description = "\n"

            position_start = content.find(semver_changelog)
            if position_start:
                position_end = content[position_start + 2 :].find("## [")
                position_end = (position_end + position_start + 2) if position_end != -1 else -1
                description = content[position_start:position_end]
                ref_start = content[position_end:].find(f"[v{semver_tag}]")
                ref_end = content[position_end + ref_start :].find("\n")
                description += "\n" + content[position_end:][ref_start:][:ref_end]

    return description


def main():
    parser = argparse.ArgumentParser(description="Upload files to gitlab tag (release)")
    parser.add_argument(
        "--server",
        default=urljoin(os.environ.get("CI_PROJECT_URL"), "/"),
        help="url of gitlab server (default: $CI_PROJECT_URL)",
    )
    parser.add_argument(
        "--project_id",
        default=os.environ.get("CI_PROJECT_ID"),
        help="Unique id of project, available in " "Project Settings/General (default: $CI_PROJECT_ID)",
    )
    parser.add_argument(
        "--release_tag",
        default=os.environ.get("CI_COMMIT_TAG"),
        help="Tag to upload files against (default: $CI_COMMIT_TAG)",
    )
    parser.add_argument("--timeout", type=int, default=120, help="Timeout for http requests")
    parser.add_argument("--ignore_cert", action="store_true", help="Ignore ssl certificate failures")
    parser.add_argument(
        "--changelog", default="CHANGELOG.md", help="CHANGELOG file, in keepachangelog format (default: CHANGELOG.md)"
    )

    parser.add_argument(
        "--job-id", default=os.environ.get("CI_JOB_ID", 0), help="Override the job number used for artifacts"
    )
    parser.add_argument("--artifact-zip", action="store_true", help="Link artifacts zip from current job")

    parser.add_argument("--zip", help="Add all files to provided zip name and upload that")
    parser.add_argument("--description", default="", help="Release description to be put in front of the files")
    parser.add_argument(
        "--link-prefix", default="", help='Prefix text added in front of each file link, eg "* " to create a list'
    )
    parser.add_argument(
        "--link-in-desc",
        action="store_true",
        help="Add the artifact links to the description. Uses release asset otherwise",
    )

    parser.add_argument("--link-artifact", action="store_true", help="Link files as artifact from the current job")

    parser.add_argument(
        "--private-token",
        default=os.environ.get("PRIVATE_TOKEN", ""),
        help="login token with permissions to commit to repo",
    )
    parser.add_argument("files", nargs="*", help="glob/s of files to upload")

    args = parser.parse_args()

    server = args.server
    if not server:
        raise SystemExit("Must provide --server if not running from CI")

    project_id = args.project_id
    if not project_id:
        raise SystemExit("Must provide --project_id if not running from CI")
    project_id = quote(project_id, safe="")

    release_tag = args.release_tag
    if not release_tag:
        raise SystemExit("Must provide --release_tag if not running from CI")

    verify = not args.ignore_cert

    print("Uploading to %s (id: %s) @ %s" % (server, project_id, release_tag))

    if not server.endswith("/"):
        server += "/"

    api_url = f"{server}api/v4/projects/{project_id}/"

    link_in_desc = args.link_in_desc or args.link_prefix

    uploads = []
    assets = []

    if args.description:
        uploads.append(args.description)

    all_files = list(itertools.chain(*[glob(f.replace("\\", "/")) if "*" in f else [f] for f in args.files]))

    if not (all_files or args.artifact_zip or args.link_artifact):
        raise SystemExit("No files found for %s" % args.files)

    token = os.environ.get("CI_JOB_TOKEN")

    private_token = args.private_token

    if all_files and not private_token and not token:
        if re.match(r"[A-Za-z0-9]", all_files[0]):
            print(
                "WARNING: legacy use of PRIVATE_TOKEN as first positional argument detected or token not supplied, please see `gitlab_release --help`"
            )
            private_token = all_files[0]
            all_files = all_files[1:]

    if all_files and private_token == all_files[0]:
        print(
            "WARNING: legacy use of PRIVATE_TOKEN as first positional argument detected, please see `gitlab_release --help`"
        )
        all_files = all_files[1:]

    if private_token:
        auth = {"PRIVATE-TOKEN": private_token}
    elif token:
        print("Using CI_JOB_TOKEN for auth")
        auth = {"JOB-TOKEN": token}
        if not args.link_artifact:
            raise SystemExit("File upload not available with CI_JOB_TOKEN, must use 'PRIVATE_TOKEN'")
    else:
        raise SystemExit(
            "Neither PRIVATE-TOKEN nor CI_JOB_TOKEN available, must be in env var 'PRIVATE_TOKEN' or provided as arg"
        )

    artifact_job = args.job_id
    if args.artifact_zip or args.link_artifact:
        if not artifact_job:
            print("Must provide --artifact-job <id> for artifact files")
            exit(-1)

        if args.link_artifact:
            for fname in all_files:
                if fname.startswith("./"):
                    fname = fname[2:]
                url = api_url + "jobs/%s/artifacts/%s" % (artifact_job, fname)

                if link_in_desc:
                    uploads.append("%s[%s](%s)" % (args.link_prefix, fname, url))
                else:
                    assets.append((fname, url))

        if args.artifact_zip:
            url = api_url + "jobs/%s/artifacts" % artifact_job
            fname = "artifact.zip"  # todo find a better name automatically?

            if link_in_desc:
                uploads.append("%s[%s](%s)" % (args.link_prefix, fname, url))
            else:
                assets.append((fname, url))

    if args.zip:
        with zipfile.ZipFile(args.zip, "w", zipfile.ZIP_DEFLATED) as zf:

            def zipdir(path, ziph):
                # ziph is zipfile handle
                for root, dirs, files in os.walk(path):
                    for file in files:
                        ziph.write(os.path.join(root, file))

            for fname in all_files:
                print(fname)
                if fname == args.zip:
                    continue
                if os.path.isdir(fname):
                    zipdir(fname, zf)
                else:
                    zf.write(fname)

        all_files = [os.path.abspath(args.zip)]

    if all_files and not args.link_artifact:
        print("Uploading %s" % all_files)

        for fname in all_files:

            with codecs.open(fname, "rb") as filehandle:
                rsp = requests.post(api_url + "uploads", files={"file": filehandle}, headers=auth, verify=verify)
                try:
                    rsp.raise_for_status()
                except Exception as ex:
                    raise SystemExit("Upload of {f} failed: {ex}".format(f=fname, ex=ex))
                else:
                    response = rsp.json()
                    if link_in_desc:
                        uploads.append("%s%s" % (args.link_prefix, response["markdown"]))
                    else:
                        assets.append((response["alt"], api_url + response["url"]))

    def fix_markdown(match):
        return "[%s](%s)" % (match.group(1), quote(match.group(2), safe="/:"))

    uploads = [re.sub(r"^\[(.*)\]\((.*)\)$", fix_markdown, u) for u in uploads]

    description = "  \n".join(uploads)

    # Now we've got the uploaded file info, attach that to the tag
    url = urljoin(api_url, "repository/tags/{t}".format(t=quote(release_tag, safe="")))
    tag_details = requests.get(url, headers=auth, verify=verify).json()

    method = requests.post
    if link_in_desc and "release" in tag_details and tag_details["release"] is not None:
        print("Update existing release")
        description = "  \n".join((tag_details["release"]["description"], description))
        method = requests.put

    description += try_to_get_changelog(args.changelog, args.release_tag)
    data = {"tag_name": release_tag, "description": description}

    if not link_in_desc:
        rsp = requests.get(api_url + "releases/" + release_tag, headers=auth, verify=verify)
        if rsp.status_code == 200:
            try:
                existing = rsp.json()
                # Updating existing.
                # It appears assets can only be added at creation, not during update (Nov 2020) so we copy existing
                # details and delete it, ready for it to be re-created with our assets below
                data["name"] = existing.get("name", release_tag)
                data["tag_name"] = existing.get("tag_name", release_tag)
                # data['description'] = existing.get('description', '') + data.get('description', '')
                if "milestones" in existing:
                    data["milestones"] = existing.get("milestones")

                requests.delete(api_url + "releases/" + release_tag, headers=auth, verify=verify)

            except Exception as ex:
                print("No existing release:", ex)

        data["assets"] = dict(links=[dict(name=name, url=url) for name, url in assets])

    if link_in_desc:
        rsp = method(url + "/release", data={"description": description}, headers=auth, verify=verify)
    else:
        rsp = method(api_url + "releases", json=data, headers=auth, verify=verify)
    try:
        rsp.raise_for_status()
        tagname = rsp.json()["tag_name"]
        print("Uploaded %s to tag %s: %s" % (all_files, tagname, urljoin(server, "tags/%s" % quote(tagname))))

    except Exception as ex:
        raise SystemExit('Uploading release failed: "{d}" error: {ex}'.format(d=description, ex=ex))


if __name__ == "__main__":
    main()
