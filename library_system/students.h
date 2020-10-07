//
// Created by zero on 2020/10/7.
// 学生信息： 学号 姓名 性别 学院 专业 借书时间
//
//
//

#ifndef LIBRARY_SYSTEM_STUDENTS_H
#define LIBRARY_SYSTEM_STUDENTS_H
#include <string>
using namespace std;
class student
{
public:
    student(){};
    student(int id,
            string name,
            bool sex,
            string academy,
            int time_left)
    {
        set_id(id);
        set_name(name);
        set_sex(sex);
        set_academy(academy);
        set_time_left(time_left);
    };
    void set_id(int input) { id = input; };
    void set_name(string input) { name = input; };
    void set_sex(bool input) { sex = input; };
    void set_academy(string input) { academy = input; };
    void set_time_left(int input) { time_left = input; };
    int get_id() { return id; };
    string get_name() { return name; };
    bool get_sex() { return sex; };
    string get_academy() { return academy; };
    int get_time_left() { return time_left; };

private:
    int id;
    string name;
    bool sex; // 1:男 0:女
    string academy;
    int time_left;
};
#endif //LIBRARY_SYSTEM_STUDENTS_H
