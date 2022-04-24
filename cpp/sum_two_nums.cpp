#include <iostream>
#include <map>
#include <unordered_map>
#include <vector>
using namespace std;

vector<int> nums = {2, 34, 7, 15, 9};

void twoNums(vector<int> nums, int target) {
  for (int i = 0; i < nums.size(); i++) {
    if (nums[i] < target) {
      for (int j = i; j < nums.size(); j++) {
        if (nums[i] + nums[j] == target) {
          cout << i << " " << j << endl;
        }
      }
    }
  }
}

void twoNums_map(vector<int> nums, int target) {
  unordered_map<int, int> A;
  for (int i = 0; i < nums.size(); i++) {
    auto it = A.find(target - nums[i]);
    if (it != A.end()) printf("%d %d\n", it->second, i);
    A.insert(pair<int, int>(nums[i], i));
  }
}
int main() {
  int target = 9;
  twoNums_map(nums, target);
  return 0;
}