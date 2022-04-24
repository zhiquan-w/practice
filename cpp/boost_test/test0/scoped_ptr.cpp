#include <boost/scoped_ptr.hpp>
#include <iostream>
using namespace std;
class X {
 public:
  X() { cout << "X ..." << endl; }
  ~X() { cout << "~X ..." << endl; }
};
int main(void) {
  cout << "Entering main ..." << endl;
  {
    boost::scoped_ptr<X> pp(new X);

    // boost::scoped_ptr<X> p2(pp); //Error:所有权不能转移
  }
  cout << "Exiting main ..." << endl;

  return 0;
}
