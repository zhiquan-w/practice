#include "library.h"

void insert_student_info(MYSQL *connect, student *input)
{
        int val = 0;
        char query[1024];
        sprintf(query, "insert into student_information (id,name,sex,academy,time) values (%d, \"%s\", \"%s\", \"%s\", \"%s\");",
                input->get_id(),
                input->get_name().c_str(),
                input->get_sex().c_str(),
                input->get_academy().c_str(),
                input->get_time().c_str());
        val = mysql_query(connect, query);
        printf("%d\n", val);
}

void delete_student_info(MYSQL *connect, student *input)
{
}

void get_student_info_by_id(MYSQL *connect, student *input)
{
        MYSQL_RES res;
        MYSQL_ROW row;
        MYSQL_FIELD *fields;
        char query[256];
        int num_fileds;
        sprintf(query, "SELECT * FROM student_information where id = %d", input->get_id());
        mysql_query(connect, query);
        res = *mysql_store_result(connect);
        num_fileds = mysql_num_fields(&res);
        row = mysql_fetch_row(&res);
        fields = mysql_fetch_fields(&res);
        for (int i = 0; i < num_fileds; i++)
        {
                if (strncmp(fields[i].name, "id", strlen("id")) == 0)
                {
                        input->set_id(atoi(row[i]));
                };
                if (strncmp(fields[i].name, "name", strlen("name")) == 0)
                {
                        input->set_name(row[i]);
                };
                if (strncmp(fields[i].name, "sex", strlen("sex")) == 0)
                {
                        input->set_sex(row[i]);
                };
                if (strncmp(fields[i].name, "academy", strlen("academy")) == 0)
                {
                        input->set_academy(row[i]);
                };
                if (strncmp(fields[i].name, "time", strlen("time")) == 0)
                {
                        input->set_time(row[i]);
                };
        }
}

void get_all_student_info(MYSQL *connect, student *input)
{
}