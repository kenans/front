document.write("\
<div style='width:230px;'>\
{%for i in images%}\
<a href='http://rabb8.com/#{{i["id"]}}'>\
<img src='{{i["image_url"]}}' style='border:solid 1px #ccc;width:100px;height:100px;padding:3px;margin:2px;'/></a>\
{%end for%}\
</div>\
");
