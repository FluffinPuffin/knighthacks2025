const forwardBtn = document.getElementById('forwardBtn');
const leftBtn = document.getElementById('leftBtn');
const rightBtn = document.getElementById('rightBtn');

forwardBtn.addEventListener('click', () => {
    console.log('Move Forward');
});

leftBtn.addEventListener('click', () => {
    console.log('Turn Left');
});

rightBtn.addEventListener('click', () => {
    console.log('Turn Right');
});
