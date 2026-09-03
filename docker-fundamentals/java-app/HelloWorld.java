import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;

public class HelloWorld {

    private static final String BODY = "<h1>Hello World from Java</h1>";

    public static void main(String[] args) throws IOException {
        int port = 8080;
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", port), 0);
        server.createContext("/", HelloWorld::handle);
        server.setExecutor(null);
        server.start();
        System.out.println("Java app listening on port " + port);
    }

    private static void handle(HttpExchange exchange) throws IOException {
        byte[] bytes = BODY.getBytes("UTF-8");
        exchange.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
        exchange.sendResponseHeaders(200, bytes.length);
        try (OutputStream out = exchange.getResponseBody()) {
            out.write(bytes);
        }
    }
}
