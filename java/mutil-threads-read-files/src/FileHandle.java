import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;

public class FileHandle {
    public static void HandleFile(File file) {
        System.out.println(Thread.currentThread().getName() + " handle file " + file.getName());

        try (FileInputStream fis = new FileInputStream(file)) {
            int b;
            int count = 0;
            while ((b = fis.read()) != -1) {
                count++;
            }
            System.out.println(Thread.currentThread().getName() + " finish file " + file.getName() + " size " + count);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        String folderPath = "D:\\files\\";
        File folder = new File(folderPath);
        File[] files = folder.listFiles();

        if (files != null) {
            Method_1.handle(files);
            Method_2.handle(files);
        }

    }
}
