import java.io.File;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

class Task implements Runnable {
    private final File file;

    public Task(File file) {
        this.file = file;
    }

    @Override
    public void run() {
        FileHandle.HandleFile(file);
    }
}

public class Method_2 {
    public static void handle(File[] files) {
        ExecutorService es = Executors.newFixedThreadPool(3);
        for (File file : files) {
            es.submit(new Task(file));
        }
        es.shutdown();
    }
}
