$(document).ready(function(){

  $(window).endlessScroll({
    fireOnce: true,
    fireDelay: true,
    loader: "<div class='loading'>LOADING...<div>",
    callback: function(p){
      load_content_more();
    }
  });

});
