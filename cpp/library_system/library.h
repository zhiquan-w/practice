#ifndef LIBRARY_SYSTEM_LIBRARY_H
#define LIBRARY_SYSTEM_LIBRARY_H
#include "students.h"
#include "stdio.h"
#include "string.h"
#include <mysql.h>

void insert_student_info(MYSQL *connect, student *input);
void delete_student_info(MYSQL *connectp, student *input);
void get_student_info_by_id(MYSQL *connect, student *input);
void get_all_student_info(MYSQL *connect, student *input);

#endif