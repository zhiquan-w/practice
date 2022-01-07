import numpy as np
import fire


def main(filename):
    res = np.load(filename)
    print(res)
    print(res.shape)


if __name__ == "__main__":
    fire.Fire(main)
