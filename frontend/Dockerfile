# 프론트엔드 Dockerfile
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# 이미지 재빌드를 위해 Dockerfile 변경 사항이 반영되었는지 확인합니다.
