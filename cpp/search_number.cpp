#include <stdio.h>

#include <vector>

using namespace std;
int main() {
  vector<char> tmp_number;
  vector<char> string;
  vector<vector<char>> all_number;
  char char_tmp;
  while (char_tmp != '\n') {
    scanf("%c", &char_tmp);
    string.push_back(char_tmp);
  }

  vector<char>::iterator it = string.begin();
  vector<char>::iterator it_tmp;
  while (it != string.end()) {
    if ('0' <= *it && *it <= '9') {
      tmp_number.push_back(*it);
      if (*(it + 1) < '0' || *(it + 1) > '9') {
        all_number.push_back(tmp_number);
        tmp_number.clear();
      }
    }
    printf("%c", *it++);
  }
  printf("\n");
  vector<vector<char>>::iterator it_all = all_number.begin();
  while (it_all != all_number.end()) {
    it_tmp = (*it_all).begin();
    while (it_tmp != (*it_all).end()) {
      printf("%c", *it_tmp++);
    }
    it_all++;
    printf(" ");
  }
  printf("\n");
  return 0;
}