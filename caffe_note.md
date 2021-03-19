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
in src/caffe/util/sampler.cpp

caffe_rng_uniform(1, 0.f, 1 - bbox_width, &w_off);
caffe_rng_uniform(1, 0.f, 1 - bbox_height, &h_off);

caffe_rng_uniform will get block, when bbox_width or bbox_height near 1.0 , (1 - bbox_width) will less than 0.f

I change the SampleBBox function, get success

void SampleBBox(const Sampler& sampler, NormalizedBBox* sampled_bbox) {
// Get random scale.
CHECK_GE(sampler.max_scale(), sampler.min_scale());
CHECK_GT(sampler.min_scale(), 0.);
CHECK_LE(sampler.max_scale(), 1.);
float scale;
caffe_rng_uniform(1, sampler.min_scale(), sampler.max_scale(), &scale);
// Get random aspect ratio.
CHECK_GE(sampler.max_aspect_ratio(), sampler.min_aspect_ratio());
CHECK_GT(sampler.min_aspect_ratio(), 0.);
CHECK_LT(sampler.max_aspect_ratio(), FLT_MAX);
float aspect_ratio;
caffe_rng_uniform(1, sampler.min_aspect_ratio(), sampler.max_aspect_ratio(),
&aspect_ratio);
aspect_ratio = std::max(aspect_ratio, std::pow(scale, 2.));
aspect_ratio = std::min(aspect_ratio, 1 / std::pow(scale, 2.));
// Figure out bbox dimension.
float bbox_width = scale * sqrt(aspect_ratio);
float bbox_height = scale / sqrt(aspect_ratio);
/*here*/
if(bbox_width>=1.0){
bbox_width=1.0;
}
if(bbox_height>=1.0){
bbox_height=1.0;
}
// Figure out top left coordinates.
float w_off, h_off;
caffe_rng_uniform(1, 0.f, 1.0f - bbox_width, &w_off);
caffe_rng_uniform(1, 0.f, 1.0f - bbox_height, &h_off);
sampled_bbox->set_xmin(w_off);
sampled_bbox->set_ymin(h_off);
sampled_bbox->set_xmax(w_off + bbox_width);
sampled_bbox->set_ymax(h_off + bbox_height);
}