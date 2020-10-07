#ifndef LIBRARY_SYSTEM_LIBRARY_H
#define LIBRARY_SYSTEM_LIBRARY_H
#include "students.h"
#include <map>

void add_student_info(map<int, student> &_map, student input);
void delete_student_info(map<int, student> &_map, int input);
map<int, student>::iterator find_student_info(map<int, student> &_map, int input);
void write_student_info(map<int, student> _map, string filename);
void read_student_info(map<int, student> &_map, string filename);
void clear_student_info(string filename);

#endif