FROM golang:1.24-alpine AS builder
WORKDIR /app
RUN apk add --no-cache git

# Копируем файлы go.mod и go.sum для зависимостей
COPY go.mod go.sum ./

# Скачиваем внешние зависимости
RUN go mod download

# Копируем весь проект
COPY . .

# Сборка
RUN go build -o server main.go

# -----------------------------
# Runtime stage
# -----------------------------
FROM alpine:latest
WORKDIR /app
RUN apk add --no-cache ca-certificates

COPY --from=builder /app/server .
COPY --from=builder /app/config ./config
COPY --from=builder /app/pac.tmpl .

EXPOSE 1080 8080
CMD ["./server"]
