# ---- build stage: needs the full JDK to compile ----
FROM eclipse-temurin:21-jdk-alpine AS build

WORKDIR /src
COPY HelloWorld.java ./
RUN javac -d /out HelloWorld.java

# ---- run stage: only needs the JRE, so the JDK is left behind ----
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app
COPY --from=build /out ./

EXPOSE 8080
CMD ["java", "HelloWorld"]
