#include <mysql.h>

#include <iostream>

#include "library.h"

using namespace std;

int main() {
  MYSQL conn;
  student A;

  int id;
  string name;
  string sex;
  string academy;
  string time;

  char confirm = 'N';

  mysql_init(&conn);
  if (!mysql_real_connect(&conn, "localhost", "root", "pppp", "library", 0,
                          NULL, 0)) {
    cout << "fail to connect mysql" << endl;
    return -1;
  }
  while (true) {
    A = {};
    cout << "1：添加学生信息" << endl;
    cout << "2：查找学生信息" << endl;
    cout << "3：删除学生信息" << endl;
    cout << "4：删除库信息" << endl;
    cout << "0：保存退出" << endl;
    cout << "请选择：" << endl;
    int cmd = 0;
    cin >> cmd;
    switch (cmd) {
      case 0:

        return 0;
      case 1:
        cout << "学号：";
        cin >> id;
        cout << "姓名：";
        cin >> name;
        cout << "性别：";
        cin >> sex;
        cout << "学院：";
        cin >> academy;
        cout << "日期：";
        cin >> time;
        A.set_id(id);
        A.set_name(name);
        A.set_sex(sex);
        A.set_academy(academy);
        A.set_time(time);
        insert_student_info(&conn, &A);
        break;
      case 2:
        cout << "学号：";
        cin >> id;
        A.set_id(id);
        get_student_info_by_id(&conn, &A);
        cout << A.get_id() << endl;
        cout << A.get_name() << endl;
        cout << A.get_sex() << endl;
        cout << A.get_academy() << endl;
        cout << A.get_time() << endl;
        break;
      case 3:
        cout << "学号：";
        cin >> id;

        break;
      case 4:
        cout << "确定要删除整个数据库吗？(Y/N)" << endl;
        cin >> confirm;
        if (confirm == 'Y') break;
      default:
        break;
    }
  }
}