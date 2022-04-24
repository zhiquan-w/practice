#include <string>
void swap(std::string& a, std::string& b) {
  std::string temp = std::move(a);
  a = std::move(b);
  b = std::move(temp);
}

#include <iostream>

int main() {
  std::string a = "abc";
  std::string b = "def";
  std::cout << a << std::endl;
  std::cout << b << std::endl;
  swap(a, b);
  std::cout << a << std::endl;
  std::cout << b << std::endl;
  return 0;
}
