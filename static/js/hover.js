// Images and alt attribute
var images = {
  image: [
    {src: 'https://unsplash.it/400/301?random', alt: 'Project 1'}
    , {src: 'https://unsplash.it/400/302?random', alt: 'Project 2'}
    , {src: 'https://unsplash.it/400/303random', alt: 'Project 3'}
    , {src: 'https://unsplash.it/400/304?random', alt: 'Project 4'}
    , {src: 'https://unsplash.it/400/305?random', alt: 'Project 5'}
    , {src: 'https://unsplash.it/400/306?random', alt: 'Project 6'}
    , {src: 'https://unsplash.it/400/307?random', alt: 'Project 7'}
    , {src: 'https://unsplash.it/400/308?random', alt: 'Project 8'}
    , {src: 'https://unsplash.it/400/309?random', alt: 'Project 9'}
  ]
};

// Show Modal Image 
function onClick(element) {
  document.getElementById("img").src = element.src;
  document.getElementById("modal").style.display = "block";
}

