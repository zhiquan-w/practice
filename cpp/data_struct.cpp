#include <iostream>
#include <string>
#include <forward_list>
#include <map>
using namespace std;

int main()
{
        forward_list<int> fl;
        fl.push_front(12); // 在开头添加元素
        fl.insert_after(fl.begin(), 11);
        //       fl.pop_front(); // 在开头删除元素
        //       fl.remove(11);  // 删除元素
        for (auto it = fl.begin(); it != fl.end(); it++)
                cout << *it << endl;
        // 红黑树实现，模拟一维哈希
        map<int, int> mm;
        mm[1] = 1;                  // 插入元素 (1,1)
        mm.insert(make_pair(2, 2)); // 插入元素 (2,2)
        mm.insert(make_pair(2, 2));
        mm.insert(make_pair(1, 1));
        for (auto itr = mm.cbegin(); itr != mm.cend(); itr++)
                cout << "(" << itr->first << "," << itr->second << ")" << endl; // 输出 (1,1) (2,2)

        // 模拟二维哈希
        map<string, map<string, int>> mmm;
        map<string, int> m;
        m.insert(make_pair("xiaoming0", 20));
        m.insert(make_pair("xiaoming1", 10));
        m.insert(make_pair("xiaoming2", 40));
        m.insert(make_pair("xiaoming3", 30));
        cout << m["xiaoming0"] << endl;

        mmm.insert(make_pair("A", m));
        for (auto it0 = mmm.begin(); it0 != mmm.end(); it0++)
        {

                for (auto it1 = it0->second.begin(); it1 != it0->second.end(); it1++)
                        cout << it1->first << " " << it1->second << endl;
        }

        return 0;
}