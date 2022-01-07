from protocol import assembler
from protocol import helper
from pymodel import cycle_model


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--eu", help="eu name, in [teng, cv, conv, wbk]", required=True)
    parser.add_argument("--ddr_bw", help="ddr bindwidth (BytePerCycle)", default=1024)
    parser.add_argument("--ocm_bw", help="ocm bindwidth (BytePerCycle)", default=1024)
    parser.add_argument("cfg_bin", metavar="cfg.bin")
    args = parser.parse_args()
    cfg_name = {"teng": "npu_teng_cfg_t*", "cv": "npu_cv_cfg_t*", "conv": "npu_conv_cfg_t*", "wbk": "npu_conv_cfg_t*"}
    process = {
        "teng": cycle_model.teng_cycle_model,
        "cv": cycle_model.cv_cycle_model,
        "conv": cycle_model.conv_cycle_model,
        "wbk": cycle_model.wbk_cycle_model,
    }
    bw = cycle_model.NPUBandwidth(ocm_bytes_per_cycle=float(args.ocm_bw), ddr_bytes_per_cycle=float(args.ddr_bw))
    # TODO: Correctly set memory types based on RDMA/WDMA start_addr.
    dma_memory_types = {d: assembler.MemoryType.OCM for d in assembler.RDMA_LIST + assembler.WDMA_LIST}
    with open(args.cfg_bin, "rb") as f:
        buffer = f.read()
        cfg = helper.from_buffer(buffer, cfg_name[args.eu])
        model = process[args.eu](cfg, dma_memory_types)
        print(model)
        print(model.total_cycles(bw))


if __name__ == "__main__":
    main()
