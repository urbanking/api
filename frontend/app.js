function processData() {
    fetch('http://backend:8000/process_data', {
      method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
      const resultDiv = document.getElementById('result');
      resultDiv.innerHTML = `
        <h3>${data.title}</h3>
        <p>작성자: ${data.writer}</p>
        <p>작성일: ${data.date}</p>
        <p>${data.content}</p>
        <p>태그: ${data.tags}</p>
        <p>공감 수: ${data.sympathy}</p>
        <p>URL: <a href="${data.post_url}" target="_blank">${data.post_url}</a></p>
        <p>광고 이미지: ${data.ad_images}</p>
        <p>광고 감지 상태: ${data.광고}</p>
        <hr>
      `;
    })
    .catch(error => {
      console.error('Error:', error);
      alert('데이터 처리 중 오류가 발생했습니다.');
    });
  }
  
  function getAllData() {
    fetch('http://backend:8000/data')
      .then(response => response.json())
      .then(data => {
        const resultDiv = document.getElementById('result');
        resultDiv.innerHTML = '';
  
        data.forEach(item => {
          const postDiv = document.createElement('div');
          postDiv.innerHTML = `
            <h3>${item.title}</h3>
            <p>작성자: ${item.writer}</p>
            <p>작성일: ${item.date}</p>
            <p>${item.content}</p>
            <p>태그: ${item.tags}</p>
            <p>공감 수: ${item.sympathy}</p>
            <p>URL: <a href="${item.post_url}" target="_blank">${item.post_url}</a></p>
            <p>광고 이미지: ${item.ad_images}</p>
            <p>광고 감지 상태: ${item.광고}</p>
            <hr>
          `;
          resultDiv.appendChild(postDiv);
        });
      })
      .catch(error => {
        console.error('Error:', error);
        alert('데이터 조회 중 오류가 발생했습니다.');
      });
  }

// WebSocket 연결 설정
let socket;

function initializeWebSocket() {
    socket = new WebSocket('ws://localhost:8000/ws');

    socket.onopen = function(event) {
        console.log('WebSocket 연결이 열렸습니다.');
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'crawl') {
            displayLiveResult(data.content);
        }
    };

    socket.onclose = function(event) {
        console.log('WebSocket 연결이 닫혔습니다.');
    };

    socket.onerror = function(error) {
        console.error('WebSocket 오류:', error);
    };
}

function submitQuery() {
    const query = document.getElementById('queryInput').value;
    if (!query) {
        alert('쿼리를 입력하세요.');
        return;
    }

    // WebSocket 초기화
    initializeWebSocket();

    fetch('http://localhost:8000/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        displayPredictions(data.predictions);
        socket.close(); // 작업 완료 후 WebSocket 연결 종료
    })
    .catch(error => {
        console.error('Error:', error);
        socket.close();
    });
}

function displayPredictions(predictions) {
    const predictionsList = document.getElementById('predictionsList');
    predictionsList.innerHTML = ''; // 기존 목록 초기화

    predictions.forEach((prediction, index) => {
        const listItem = document.createElement('li');
        listItem.textContent = `글 ${index + 1}: ${prediction}`;
        predictionsList.appendChild(listItem);
    });
}

function displayLiveResult(content) {
    const liveResultsList = document.getElementById('liveResultsList');
    const listItem = document.createElement('li');
    listItem.textContent = content;
    liveResultsList.appendChild(listItem);
}
