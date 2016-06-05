document.write("\
<div style='background-color:#ccc;width:320px;'>\
{%for i in images%}\
<a href='http://rabb8.com/#{{i["id"]}}'>\
<img src='{{i["image_url"]}}' style='width:150px;height:150px;margin:5px;'/></a>\
{%end for%}\
</div>\
");
