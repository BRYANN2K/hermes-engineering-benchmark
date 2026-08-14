const voter=localStorage.voter||(localStorage.voter=crypto.randomUUID());const data=await fetch('/api/poll').then(r=>r.json());document.querySelector('#total').textContent=`${data.totalVotes} votes`;
