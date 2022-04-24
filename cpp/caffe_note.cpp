## 1.caffe python/caffe/proto/caffe_pb2.py 
DESCRIPTOR = _descriptor.FileDescriptor(
  name='caffe/proto/caffe.proto', # 注意路径
  package='caffe',
  syntax='proto2',

## 2.math_functions.cpp:250] Check failed: a <= b (0 vs. -1.19209e-07) 
void caffe_rng_uniform(const int n, const Dtype a, const Dtype b, Dtype* r) {
  CHECK_GE(n, 0);
  CHECK(r);
  // CHECK_LE(a, b);
  boost::uniform_real<Dtype> random_distribution(a, caffe_nextafter<Dtype>(b));
  boost::variate_generator<caffe::rng_t*, boost::uniform_real<Dtype> >
      variate_generator(caffe_rng(), random_distribution);
  for (int i = 0; i < n; ++i) {
    r[i] = variate_generator();
  }
}

## 3.blocking_queue.cpp:50] Data layer prefetch queue empty
#找到文件 / data / VOC0712 / create_data.sh ，将width = 0改为width = \
    300，将height = 0改为height = 300.
