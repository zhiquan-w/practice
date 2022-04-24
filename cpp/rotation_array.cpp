#include <iostream>
#include <vector>
using namespace std;
vector<vector<int>> x = {{5, 1, 9, 11, 2},
                         {2, 4, 8, 10, 2},
                         {13, 3, 6, 7, 2},
                         {15, 14, 12, 16, 2},
                         {1, 2, 3, 4, 5}};
class Solution {
 public:
  void swap(int &x, int &y) {
    int tmp = x;
    x = y;
    y = tmp;
  }
  void rotate(vector<vector<int>> &matrix) {
    unsigned int n = matrix.size();
    unsigned int tmp = 0;
    for (unsigned int i = 0; i < (n + 1) / 2; i++) {
      for (unsigned int j = i; j < n - 1 - i; j++) {
        swap(matrix[i][j], matrix[j][n - 1 - i]);
        swap(matrix[i][j], matrix[n - 1 - i][n - 1 - j]);
        swap(matrix[i][j], matrix[n - 1 - j][i]);
      }
    }
  }
};
int main() {
  Solution A;
  A.rotate(x);
  for (int i = 0; i < x.size(); i++) {
    for (int j = 0; j < x[i].size(); j++) {
      cout << x[i][j] << " ";
    }
    cout << endl;
  }

  return 0;
}