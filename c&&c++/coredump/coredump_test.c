/*
gcc -g -o bin_coredump coredump_test.c
*/

#include <stdio.h>
#include <stdlib.h> // exit
#include <string.h> // sprintf
#include <unistd.h> // sleep
#include <signal.h> // signal

struct student {
    char name[50];
    int age;
};

struct student *g_stu = NULL;
struct student *g_students = NULL;
#define MAX_NUM (10)

static void signal_handler(int sig) {
    static int count = 0;
    printf("%s enter sig %d\n", __FUNCTION__, sig);
    count++;
    
    if (sig == SIGSEGV) {
        abort();
    }
    
    if (count >= 10) {
        exit(0);
    }
}

int main() {
    signal(SIGSEGV, signal_handler);

    g_stu = (struct student *)malloc(MAX_NUM * MAX_NUM * MAX_NUM * sizeof(struct student)); // 测试堆内存转储
    if (g_stu == NULL) {
        printf("g_stu NULL\n");
        exit(0);
    }
    
    struct student students[MAX_NUM * MAX_NUM]; // 测试栈内存转储
    for(int i = 0; i < MAX_NUM * MAX_NUM; i++) {
        sprintf(g_students[i].name, "local_%d", i);
        g_students[i].age = i;
        printf("name %s, age %d\n", g_students[i].name, g_students[i].age);
    }

    g_students = (struct student *)malloc(MAX_NUM * sizeof(struct student)); // 测试堆内存转储
    if (g_students == NULL) {
        printf("g_students NULL\n");
        exit(0);
    }
    
    for(int i = 0; i < MAX_NUM; i++) {
        sprintf(g_students[i].name, "global_%d", i);
        g_students[i].age = i;
        printf("name %s, age %d\n", g_students[i].name, g_students[i].age);
    }

    free(g_stu);
    g_stu = NULL;

    free(g_students);
    g_students = NULL;

    // to coredump
    printf("name %s, age %d\n", g_students[0].name, g_students[0].age);
    
    return 0;
}