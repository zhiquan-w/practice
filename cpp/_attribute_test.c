#include <stdio.h>

typedef struct {
    int a;
    char b;
    long int c[10];
} testA;

typedef struct {
    int a;
    char b;
    long int c[10];
} __attribute__((packed)) testB;
#pragma pack(1)
typedef struct {
    int a;
    char b;
    long int c[10];
} testC;
#pragma pack()
int main() {
    testA A;
    testB B;
    testC C;
    printf("testA size %ld \n", sizeof(A));
    printf("testB size %ld \n", sizeof(B));
    printf("testC size %ld \n", sizeof(C));
    return 0;
}
