# 编译该工程CMAKE最低版本
CMAKE_MINIMUM_REQUIRED(VERSION 3.2 FATAL_ERROR)
# 工程名字
PROJECT(library)
# 指定生成目标
ADD_EXECUTABLE(library main.cpp library.cpp students.cpp)
# 为指定的bin文件添加三方链接库
# TARGET_LINK_LIBRARIES(opencv_test)