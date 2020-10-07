#include <iostream>
#include "library.h"

using namespace std;

int main()
{
        map<int, student> library;
        student A;
        map<int, student>::iterator it;
        string filename = "1.txt";
        int id;
        string name;
        bool sex;
        string academy;
        int time;
        char confirm = 'N';
        read_student_info(library, filename);
        while (true)
        {
                A = {};
                cout << "1：添加学生信息" << endl;
                cout << "2：查找学生信息" << endl;
                cout << "3：删除学生信息" << endl;
                cout << "4：删除库信息" << endl;
                cout << "0：保存退出" << endl;
                cout << "请选择：" << endl;
                int cmd = 0;
                cin >> cmd;
                switch (cmd)
                {
                case 0:
                        clear_student_info(filename);
                        write_student_info(library, filename);
                        return 0;
                case 1:
                        cout << "学号：";
                        cin >> id;
                        read_student_info(library, filename);
                        if (find_student_info(library, id) != library.end())
                        {
                                cout << "已经存在！" << endl;
                                break;
                        }
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
                        A.set_time_left(time);
                        add_student_info(library, A);
                        break;
                case 2:
                        cout << "学号：";
                        cin >> id;
                        read_student_info(library, filename);
                        it = find_student_info(library, id);
                        if (it == library.end())
                        {
                                cout << "不存在！" << endl;
                                break;
                        }
                        cout << "学号：";
                        cout << it->second.get_id() << endl;
                        cout << "姓名：";
                        cout << it->second.get_name() << endl;
                        cout << "性别：";
                        cout << it->second.get_sex() << endl;
                        cout << "学院：";
                        cout << it->second.get_academy() << endl;
                        cout << "日期：";
                        cout << it->second.get_time_left() << endl;
                        break;
                case 3:
                        cout << "学号：";
                        cin >> id;
                        delete_student_info(library, id);
                        break;
                case 4:
                        cout << "确定要删除整个数据库吗？(Y/N)" << endl;
                        cin >> confirm;
                        if (confirm == 'Y')
                                clear_student_info(filename);
                        break;
                default:
                        break;
                }
        }
}