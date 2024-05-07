import java.io.File;

public class Method_1 {
    public static void handle(File[] files) {
        final int THREAD_COUNT = 3;
        int fileIndex = 0;

        while (files != null && fileIndex < files.length) {
            try {
                Thread[] threads = new Thread[THREAD_COUNT];
                for (int i = 0; i < THREAD_COUNT && fileIndex < files.length; i++) {
                    File file = files[fileIndex];
                    threads[i] = new Thread(() -> {
                        FileHandle.HandleFile(file);
                    });
                    threads[i].start();
                    fileIndex++;
                }

                for (Thread thread : threads) {
                    if (thread != null) {
                        thread.join();
                    }
                }
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }
}
