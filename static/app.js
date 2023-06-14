// Array of language objects
var languages = [
    { name: "en",},
    { name: "fr",},
    { name: "id",},
  
  ];
  
  function generateLanguageFlags(languages) {
    var flagsHTML = "";
  
    for (var i = 0; i < languages.length; i++) {
      var language = languages[i];
      var flagHTML = '<li class="nav-item">';
      flagHTML += '<a href="/' + language.name + '">';
      flagHTML += '<img class="flags" src="/static/flags/' + language.name + '.png" alt="' + language.name + '">';
      flagHTML += '</a>';
      flagHTML += '</li>';
  
      flagsHTML += flagHTML;
    }
  
    return flagsHTML;
  }
  var container = document.getElementById("flagsContainer");
  //container.innerHTML = generateLanguageFlags(languages);
  