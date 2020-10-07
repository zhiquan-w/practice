#include "library.h"
#include <iostream>
#include <fstream>
using namespace std;

void add_student_info(map<int, student> &_map, student input)
{
        _map.insert(make_pair(input.get_id(), input));
}

void delete_student_info(map<int, student> &_map, int input)
{
        _map.erase(input);
}

map<int, student>::iterator find_student_info(map<int, student> &_map, int input)
{
        return _map.find(input);
}

void read_student_info(map<int, student> &_map, string filename)
{
        ifstream infile;
        student tmp;
        int id;
        string name;
        bool sex;
        string academy;
        int time;
        int id_key;

        infile.open(filename, ios::in);
        while (infile.good() && !infile.eof())
        {
                infile >> id_key >> id >> name >> sex >> academy >> time;
                tmp.set_id(id);
                tmp.set_name(name);
                tmp.set_sex(sex);
                tmp.set_academy(academy);
                tmp.set_time_left(time);
                add_student_info(_map, tmp);
        }
        infile.close();
}

void write_student_info(map<int, student> _map, string filename)
{
        ofstream outfile;
        outfile.open(filename, ios::out | ios::app);
        for (auto it = _map.begin(); it != _map.end(); it++)
        {
                outfile << it->first << " " << it->second.get_id() << " ";
                outfile << it->second.get_name() << " " << it->second.get_sex() << " ";
                outfile << it->second.get_academy() << " " << it->second.get_time_left() << endl;
        }
        outfile.close();
}

void clear_student_info(string filename)
{
        ofstream outfile;
        outfile.open(filename, ios::out | ios::trunc);
        outfile.close();
}