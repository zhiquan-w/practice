onnx=$(wildcard *.onnx)

all: convert quant

convert:
	convert_tool -f onnx -m ${onnx} -o ./test.tmfile
quant:
	quant_tool_int8  -m ./test.tmfile -i ./dataset -o ./test_int8.tmfile -g 3,224,224 -w 104.007,116.669,122.679 -s 0.017,0.017,0.017
quant_perchannel:
	quant_tool_uint8_perchannel -m ./test.tmfile -i ./dataset -o ./test_int8.tmfile -g 3,224,224 -w 104.007,116.669,122.679 -s 0.017,0.017,0.017
	
