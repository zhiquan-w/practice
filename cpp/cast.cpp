#include <iostream>
#include <vector>
#include <time.h>
#include <string.h>
#include <typeinfo>
using namespace std;
 
void *do_work(void *buf){
	//1.void* ---> vector<char>.data()=char*
	char* p = (char*)(buf);
	printf("xxx---->%s(), line = %d, p->data() = %s\n",__FUNCTION__,__LINE__,p);
 
	//2.void* ---> vector<char>.data()=char*
	char* pt = static_cast<char*>(buf);
	printf("xxx---->%s(), line = %d, pt->data() = %s\n",__FUNCTION__,__LINE__,pt);
}
 
int main(){
	pthread_t td;
  char buffer[] = "Hello anbox!!!!!!!!!";
  vector<char> data(buffer, buffer + strlen(buffer));
 
	printf("data.data() = %s\n",data.data());
 
  //1.vector<char>.data()=char* ---> void*
	//pthread_create(&td,NULL,do_work, (void*)(data.data()));
 
	//2.vector<char>.data()=char* ---> void*
	pthread_create(&td,NULL,do_work, static_cast<void*>(data.data()));
	pthread_join(td, NULL);
}
