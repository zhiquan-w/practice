#include <iostream>

using namespace std;
class A {
public:
	int aa;
	A(int a) : aa(a) {}
};

int main(){
	A a(10);
	A b('a');
	cout << a.aa << endl;
	cout << b.aa << endl;
	return 0;
}
