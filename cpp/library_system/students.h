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
class student {
   public:
    student(){};
    student(int id, string name, string sex, string academy, string time_left) {
        set_id(id);
        set_name(name);
        set_sex(sex);
        set_academy(academy);
        set_time(time_left);
    };
    void set_id(int input) { id = input; };
    void set_name(string input) { name = input; };
    void set_sex(string input) { sex = input; };
    void set_academy(string input) { academy = input; };
    void set_time(string input) { time = input; };
    int get_id() { return id; };
    string get_name() { return name; };
    string get_sex() { return sex; };
    string get_academy() { return academy; };
    string get_time() { return time; };

   private:
    int id;
    string name;
    string sex;  // 1:男 0:女
    string academy;
    string time;
};
#endif  // LIBRARY_SYSTEM_STUDENTS_H
