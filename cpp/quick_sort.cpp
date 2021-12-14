#include <iostream>

using namespace std;


int partition(int *ar, int l, int h) {
    int anchor = ar[l];
    while(l < h) {
        while(ar[h] >= anchor && l < h) {
            h--;
        }
        ar[l] = ar[h];
        while(ar[l] <= anchor && l < h) {
            l++;
        }
        ar[h] = ar[l];
    }
    ar[l] = anchor;
    return l;
}
void quick_sort(int *ar, int l, int h) {
    if (l < h) {
        int anchor = partition(ar, l, h);
        cout << anchor << " " << l << " " << h << endl;
        quick_sort(ar, l, anchor-1);
        quick_sort(ar, anchor+1, h);
    }
}

int main() {
    int a[5] = {5,3,1,2,4};
    quick_sort(a, 0, 4);
    for (int i = 0;i<5;++i) {
        cout << a[i] << endl;
    }
    return 0;
}