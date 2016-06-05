document.write("\
<div style='width:110px;'>\
{%for i in images%}\
<a href='http://rabb8.com/#{{i["id"]}}'>\
<img src='{{i["image_url"]}}' style='border:solid 1px #ccc;width:100px;height:100px;padding:5px;'/></a>\
{%end for%}\
</div>\
");
