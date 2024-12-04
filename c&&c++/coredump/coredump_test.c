/*
gcc -g -o bin_coredump coredump_test.c
*/

#include <stdio.h>
#include <stdlib.h> // exit
#include <string.h> // sprintf
#include <unistd.h> // sleep
#include <signal.h> // signal
#include <sys/resource.h> // struct rlimit // -lc

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
        // 按ai的说法是在接管信号的函数里调用abort从而强制转储.
        // 实际上如果接管信号的处理函数没有是程序退出, 内核会一直给程序发送信号
        // 这是只需要在接管信号的函数里还原信号处理方式, 就能在程序下一次收到信号时生成core文件
        // ai并不总是靠谱的
        // abort();

        // 由于捕捉到信号不退出,进程会反复收到这个信号,
        // 因此在第一次处理完后还原信号处理方式到系统默认即可生成转储文件.
        printf("%s enter count %d\n", __FUNCTION__, count);
        //signal(SIGSEGV, SIG_DFL);
    }
    
    if (count >= 10) {
        //exit(0);
    }
}

int main() {
    struct rlimit limit;
    getrlimit(RLIMIT_CORE, &limit);
    //printf("rlim_cur %d,  enter sig %d\n", __FUNCTION__, sig);

    signal(SIGSEGV, signal_handler);

    g_stu = (struct student *)malloc(MAX_NUM * MAX_NUM * MAX_NUM * sizeof(struct student)); // 测试堆内存转储
    if (g_stu == NULL) {
        printf("g_stu NULL\n");
        exit(0);
    }
    
    struct student students[MAX_NUM * MAX_NUM]; // 测试栈内存转储
    for(int i = 0; i < MAX_NUM * MAX_NUM; i++) {
        sprintf(students[i].name, "local_%d", i);
        students[i].age = i;
        printf("name %s, age %d\n", students[i].name, students[i].age);
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