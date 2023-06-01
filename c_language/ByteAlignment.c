/*
1.字节对齐
做了一个关于TTS的需求涉及到音频流的处理, 需求实现后发现音频播放有电流声(杂音).
后逐步还原代码更改, 发现更改了编码输出结构体成员的数据类型导致了bug.
程序抽象如下:
 */

#include <stdio.h>
#include <string.h>
#include <stddef.h>

#define BUFF_LEN 512
typedef struct {
    unsigned char format;
    unsigned char payloadLen;
    unsigned char payloadType;
    unsigned char payload[BUFF_LEN];
} EncodeOutBuff;

void sendAudioStream(char *sendBuff, int offset, int len) {
    char buff[BUFF_LEN] = {0};
    memcpy_s(buff, sizeof(buff), sendBuff + offset, len);
    printf("buff: %d, [%s]\n", strlen(buff), buff);
}

int main() {
    printf("Hello, World! %zu\n", sizeof(EncodeOutBuff));
    printf("Hello, World! %zu\n", offsetof(EncodeOutBuff, format));
    printf("Hello, World! %zu\n", offsetof(EncodeOutBuff, payloadLen));
    printf("Hello, World! %zu\n", offsetof(EncodeOutBuff, payloadType));
    printf("Hello, World! %zu\n", offsetof(EncodeOutBuff, payload));

    EncodeOutBuff encodeOutBuff; // 编码后的音频流数据保存
    encodeOutBuff.format = 'x';
    encodeOutBuff.payloadType = 'y';

    // 原有代码正常处理G711, 处理G711编解码数据时,采样率为8000, 位深为8bit, 则10ms处理的数据长度是80.
    char *dataAfterG711Encode = "12345678910111213141516171819202122232425262728293031323334353637383940414243444"; // 示例数据,长度80
    memcpy_s(encodeOutBuff.payload, sizeof(encodeOutBuff.payload), dataAfterG711Encode, strlen(dataAfterG711Encode));
    encodeOutBuff.payloadLen = strlen(dataAfterG711Encode); // 80
    sendAudioStream(&encodeOutBuff, sizeof(EncodeOutBuff) - BUFF_LEN, encodeOutBuff.payloadLen);

    // 新增代码需要处理PCM, 处理PCM编解码数据时, 采样率为16000,位深为16bit,则10ms处理的数据长度是320.
    char *dataAfterPCMEncode = "12345678910111213141516171819202122232425262728293031323334353637383940414243444" \
                               "54647484950515253545556575859606162636465666768697071727374757677787980818283848" \
                               "58687888990919293949596979899100101102103104105106107108109110111112113114115116" \
                               "11711811912012112212312412512612712812913013113213313413513613713813914014114214"; // 示例数据,长度320
    memcpy_s(encodeOutBuff.payload, sizeof(encodeOutBuff.payload), dataAfterPCMEncode, strlen(dataAfterPCMEncode));
    encodeOutBuff.payloadLen = strlen(dataAfterPCMEncode); // 320
    sendAudioStream(&encodeOutBuff, sizeof(EncodeOutBuff) - BUFF_LEN, encodeOutBuff.payloadLen);
    return 0;
}

/*
 *  处理PCM时, 发现sendAudioStream里面printf的strlen(buff)是64, 很奇怪明明传的是320, 但是打印出来的是64.
 *  其实,这时候如果是老司机够敏感的话, 应该能立马想到数据溢出了. payloadLen一个字节,范围0~255, 320超过了255, 溢出后即为64个字节.
 *  好, 马上修改payloadLen的数据类型为unsigned short, 问题解决.
 *  typedef struct {
    unsigned char format;
    unsigned short payloadLen;
    unsigned char payloadType;
    unsigned char payload[BUFF_LEN];
} EncodeOutBuff;
 */

/*
 *  修改数据类型后, 上一个问题解决, 但是拨测发现播放的音频流有电流声, 有杂音. 即使是还原pcm相关的代码后依然有杂音
 *  测试G711流程, 对比原始编码码流dataAfterG711Encode和buff发现, buff始终丢了第一个字节.
 *  对程序进行gdb发现, sendAudioStream的第二个参数居然不是4, 而是6...........也就是不是从encodeOutBuff.payload开始读的
 *  通过offsetof打印结构体偏移量发现format占用2个字节, 而且payload的偏移量居然是5!!!!!
 */

/*
 * 查阅资料发现, 字节对齐的三个基本原则
1) 结构体变量的首地址能够被其最宽基本类型成员的大小所整除；
2) 结构体每个成员相对于结构体首地址的偏移量都是成员大小的整数倍，如有需要编译器会在成员之间加上填充字节；例如上面第二个结构体变量的地址空间。
3) 结构体的总大小为结构体最宽基本类型成员大小的整数倍，如有需要编译器会在最末一个成员之后加上填充字节。
 *
 * 由3)知, payloadLen的数据类型为unsigned short后, 结构体对齐方式改为2字节对齐,
 * 所以format占用2个字节, payloadLen占用2个字节, payloadType占用1个字节, payload占用512个字节.同时payload后有一个填充字节.
 *
 * 解决办法是结构体定义前增加#pragma pack(1), 后增加#pragma pack() 强制结构体1字节对齐.
 */

