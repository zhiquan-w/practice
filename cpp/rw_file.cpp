//This program uses the write and read functions.
#include <iostream>
#include <fstream>
using namespace std;
struct A
{
	int a;
	char b;
};


int main()
{
    //File object used to access file
    fstream file("nums.dat", ios::out | ios::binary);
    if (!file)
    {
        cout << "Error opening file.";
        return 0;
    }
    //Integer data to write to binary file
    //int buffer[ ] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    struct A buffer[2];
    for (int i = 0;i < 2;i++) {
	    buffer[i].a = i;
	    buffer[i].b = 'A';
    }
    int size = sizeof(buffer) / sizeof(buffer[0]);
    // Write the data and close the file
    cout << "Now writing the data to the file.\n";
    file.write(reinterpret_cast<char *>(buffer), sizeof(buffer));
    file.close ();
    // Open the file and use a binary read to read contents of the file into an array
    file.open("nums.dat", ios::in);
    if (!file)
    {
        cout << "Error opening file.";
        return 0;
    }
    cout << "Now reading the data back into memory.\n";
    char * buffer0 = new char(sizeof(buffer));
    file.read(reinterpret_cast<char *>(buffer0), sizeof (buffer));
    struct A * ss = (struct A*)buffer0;
    // Write out the array entries
    for (int count = 0; count < 2; count++) {
        cout << ss[count].a << " ";
        cout << ss[count].b << endl;
    }
    // Close the file
    file.close ();
    return 0;
}
