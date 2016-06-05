$(function(){
    var IMAGE_WIDTH = 248;

    var galleries;
    var source_url;
    var collection;
    var collection_set;

    var current_collection_id;
    var current_collection_liked;
    var current_board_id;
    var current_column_index;
    var current_page;
    var current_column_number = 5;

    var image_template = _.template($('#image-template').html());
    var option_template = _.template($('#option-template').html());
    var comment_template = _.template($('#comment-template').html());
    var collection_template = _.template($('#collection-template').html());

    id = window.location.pathname.replace("/", "");
    if(id){
        window.location.href = "//" + window.location.host + "/#" + id;
    }

    function image_height(width, height, thumb_width){
        return thumb_width/width*height;
    };

    function getHash() {
        var hash = window.location.hash;
        return hash.substring(1); // remove #
    }

    function removeHash () {
        var scrollV, scrollH, loc = window.location;
        if ("pushState" in history)
            history.pushState("", document.title, loc.pathname + loc.search);
        else {
            // Prevent scrolling by storing the page's current scroll offset
            scrollV = document.body.scrollTop;
            scrollH = document.body.scrollLeft;

            loc.hash = "";

            // Restore the scroll offset, should be flicker free
            document.body.scrollTop = scrollV;
            document.body.scrollLeft = scrollH;
        }
    }

    function checkURL(value) {
        var urlregex = new RegExp("^(http:\/\/|https:\/\/){1}([0-9A-Za-z]+\.)");
        if(urlregex.test(value)){
            return true;
        }
        return false;
    }

    $(".facebook").click(function(){
        window.location = "/auth/facebook?next="+next;
    });

    $(".google").click(function(){
        window.location = "/auth/google?next="+next;
    });

    $("#url").keypress(function(e) {
        if(e.keyCode == 13) {
            $("#get").click();
        }
    });

    $("#get").click(function(){
        var url = $("#url").val();
        if(!checkURL(url)){
            $("#message").show()
                .text("URL incorrect!")
                .delay(2000)
                .fadeOut();

            return;
        }

        $("#selector").slideDown();

        $.getJSON("/api/get", {"url": url}, function(data){
            $("#save").fadeIn();
            $("#close").fadeIn();

            $("#select .ad-thumb-list").empty();
            //$("#select .ad-image-wrapper").empty();

            for(i in data["images"]){
                $("#select .ad-thumb-list").append(image_template({"id": i, "url": data["images"][i]["src"]}));
            }
            if(galleries && galleries[0]){
                galleries[0].images = [];
                galleries[0].img_container = [];
            }
            galleries = $('#select.ad-gallery').adGallery({
                loader_image: '/static/loader.gif',
                //width: 780,
                height: 334,
                display_next_and_prev: true
            });
            source_url = data['url'];
        });

        load_boards();
    });

    $(".save").click(function(){
        var board_id = $("select#boards").val().slice(5);
        var board_body = $("#board_body").val();
        gallery = galleries[0];
        current_image = gallery.images[gallery.current_index];

        $.post("/api/collection", {
            "title": "",
            "body": board_body,
            "width": current_image.size.width,
            "height": current_image.size.height,
            "image_url": current_image.image,
            "source_url": source_url,
            "board_id": board_id
        }, function(data){
            //re-render
            $(".close").click();
            load_content();
        });
    });

    $(".close").click(function(){
        $("#selector").slideUp();
        $("#save").hide();
        $("#close").hide();
    });

    function show_content(content){
        current_collection_id = content["id"];

        $("#overlay").show();
        $("#spotlight_box").show();

        $("#spotlight_box #body").text(content["body"]);

        $("#spotlight_box #source_url").attr("href", content["source_url"]);
        $("#spotlight_box #source_url").text(content["source_url"]);

        if("liked" in content){
            current_collection_liked = content["liked"];
            $("#spotlight_box #like").show();
            $("#spotlight_box #like").attr("disabled", current_collection_liked);
        }else{
            $("#spotlight_box #like").hide();
        }

        user_id = content["user_id"];
        if(current_user_id == user_id){
            $("#spotlight_box #delete").show();
        }

        $("#show .ad-thumb-list").empty();
        $("#show .ad-thumb-list").append(image_template({"id": content["id"], "url": content["image_url"]}));
        height = Math.min(image_height(content["width"], content["height"], 780), content["height"])

        if(galleries && galleries[0]){
            galleries[0].images = [];
            galleries[0].img_container = [];
        }
        galleries = $('#show.ad-gallery').adGallery({
            loader_image: '/static/loader.gif',
            width: 780,
            height: height,
            display_next_and_prev: false
        });
        $('#show.ad-gallery').show();

        //FB and twitter
        $("#spotlight_box #spotlight_fb_like").empty();
        $("#spotlight_box #spotlight_fb_like").append('<fb:like send="false" width="160" show_faces="true" layout="button_count" href="'+window.location.href+'"/>');
        //$("#spotlight_box #spotlight_fb_like fb:like").attr("href", window.location.href);
        if(typeof(FB) != "undefined"){
            FB.XFBML.parse(document.getElementById('spotlight_fb_like'));
        }

        $("#spotlight_box #spotlight_twitter_share").empty();
        $("#spotlight_box #spotlight_twitter_share").append('<a href="https://twitter.com/share" class="twitter-share-button" data-url="'+window.location.href+'"></a>');
        if(typeof(twttr) != "undefined"){
            twttr.widgets.load();
        }

        $("#spotlight_box #spotlight_twitter_share a").attr("data-url", window.location.href);

        load_comments();
    }

    $("#content").on("click", ".collection", function(){
        var collection_id = this.id.slice(10);
        show_content(collection_set[collection_id]);
    });

    $("#overlay,#close_btn").click(function(){
        //window.location.href = "";
        removeHash();

        $("#overlay").hide();
        $("#spotlight_box").hide();
        $("#create_box").hide();
        $("#edit_box").hide();

        $("#close").click();
    });

    function render(data) {
        collection = [];
        collection_set = {};
        var column_index = 1;
        for(i in data["collection"]){
            var vars = data["collection"][i];
            vars["thumb_height"] = image_height(vars["width"], vars["height"], IMAGE_WIDTH);
            vars["thumb_width"] = IMAGE_WIDTH;
            collection.push(vars);
            collection_set[vars["id"]] = vars;

            $("#column" + column_index).append(collection_template(vars));
            if(++column_index > current_column_number) column_index = 1;
        }
        current_column_index = column_index;
    }

    function render_append(data) {
        var column_index = current_column_index;
        for(i in data["collection"]){
            var vars = data["collection"][i];
            //console.log(vars["id"]);
            if(!(vars["id"] in collection_set)){
                vars["thumb_height"] = image_height(vars["width"], vars["height"], IMAGE_WIDTH);
                vars["thumb_width"] = IMAGE_WIDTH;
                collection.push(vars);
                collection_set[vars["id"]] = vars;

                $("#column" + column_index).append(collection_template(vars));
                if(++column_index > current_column_number) column_index = 1;
            }
        }
        current_column_index = column_index;
    }

    function reload_by_width() {
        if($(window).width() >= 1400){
            $("#column5").show();
            $("#content").css("width", "1400px");
            current_column_number = 5;
        }else{
            $("#column5").hide();
            $("#content").css("width", "1120px");
            current_column_number = 4;
        }

        $("#column1,#column2,#column3,#column4,#column5").empty();
        var column_index = 1;
        for(i in collection){
            var vars = collection[i];
            vars["thumb_height"] = image_height(vars["width"], vars["height"], IMAGE_WIDTH);
            vars["thumb_width"] = IMAGE_WIDTH;

            $("#column" + column_index).append(collection_template(vars));
            if(++column_index > current_column_number) column_index = 1;
        }
        current_column_index = column_index;
    }

    function load_content() {
        $("#column1,#column2,#column3,#column4,#column5").empty();
        $.getJSON(API_WALL, function(data){
            render(data);
            reload_by_width();
            current_page = 1;

            var id=getHash();
            if(!id) {
            }else if(id in collection_set){
                $("#collection"+id).click();
            }else{
                $.getJSON("/api/collection?id="+id, function(data){
                    show_content(data);
                });
            }
        });
    }

    function load_content_more() {
        $.getJSON(API_WALL+"?page="+current_page, function(data){
            render_append(data);
            current_page++;
        });
    }

    function load_boards() {
        $("#boards").empty();
        $.getJSON("/api/boards", function(data){
            if(data["boards"] && data["boards"].length > 0){
                $("#boards").empty();
                for(i in data["boards"]){
                    var option = data["boards"][i];
                    option["value"] = "board"+data["boards"][i]["id"];
                    $("#boards").append(option_template(option));
                }
            }else if(data["boards"] && data["boards"].length == 0){
                $("#overlay").show();
                $("#create_box").show();
            }else{}
        });
    }

    function load_comments() {
        $.getJSON("/api/comments?id="+current_collection_id, function(data){
            $("#spotlight_box #comments").empty();
            for(i in data["comments"]){
                $("#spotlight_box #comments").append(comment_template(data["comments"][i]));
            }
        });
    }

    $("#new_board").click(function(){
        $("#edit_box").hide();
        $("#create_box").show();
    });

    $("#create_board").click(function(){
        var name = $("#create_box input.board_name").val();
        var category_id = $("#create_box select.categories").val().slice(8);

        if(name){
            $.ajax({
                url: "/api/boards",
                data: {"name":name, "category_id":category_id},
                type: "put",
                success: function(data){
                    $("#message").show()
                                 .text("You created a board!")
                                 .delay(2000)
                                 .fadeOut();

                    load_boards();
                    $("#overlay").hide();
                    $("#create_box").hide();
                }
            });
        }else{
            //need board name
        }
    });

    $("#save_board").click(function(){
        //var board_id = $("#edit_box input.board_id").val();
        var board_id = current_board_id;
        var name = $("#edit_box input.board_name").val();
        var category_id = $("#edit_box select.categories").val().slice(8);

        if(name){
            $.ajax({
                url: "/api/boards",
                data: {"board_id":board_id, "name":name, "category_id":category_id},
                type: "post",
                success: function(data){
                    $("#message").show()
                                 .text("You updated a board!")
                                 .delay(2000)
                                 .fadeOut();

                    $("#cancel_board").click();
                    load_boards();
                }
            });
        }else{
            //need board name
        }
    });

    $("#cancel_board").click(function(){
        $("#overlay").hide();
        $("#edit_box").hide();
    });

    /*
    $("#delete_board").click(function(){
        //var board_id = $("#edit_box input.board_id").val();
        var board_id = current_board_id;
        var name = $("#edit_box input.board_name").val();
        var category_id = $("#edit_box select.categories").val().slice(8);

        if(name){
            $.ajax({
                url: "/api/boards",
                data: {"board_id":board_id, "name":name, "category_id":category_id},
                type: "delete",
                success: function(data){
                    $("#message").show()
                                 .text("You delete a board!")
                                 .delay(2000)
                                 .fadeOut();
                }
            });
        }else{
            //need board name
        }
    });
    */

    $("#edit_board").click(function(){
        $("#overlay").show();
        $("#edit_box").show();

        var board_id = $("select#boards").val().slice(5);
        //$("#edit_box input.board_id").val(board_id);
        current_board_id = board_id;

        var board_name = $("select#boards option:selected").text();
        $("#edit_box .board_name").val(board_name);

        $.getJSON("/api/boards?id="+board_id, function(data){
            var category_id = data["board"]["category_id"];
            $("#edit_box .categories").val("category"+category_id);
        });
    });

    $("#spotlight_box #like").click(function(){
        var collection_id = current_collection_id;
        $.post("/api/like", {"id": collection_id}, function(){
            $("#message").show()
                         .text("You liked it!")
                         .delay(2000)
                         .fadeOut();

            var i = collection_set[collection_id];
            i["liked"] = true;
            $("#spotlight_box #like").attr("disabled", true);

            load_content();
        });
    });

    $("#spotlight_box #edit").click(function(){
        var collection_id = current_collection_id;
        /*
        $.post("/api/like", {"id": collection_id}, function(){
            $("#message").show()
                         .text("You liked it!")
                         .delay(2000)
                         .fadeOut();

            var i = collection_set[collection_id];
            i["liked"] = true;
            $("#spotlight_box #like").attr("disabled", true);

            load_content();
        });
        */
    });

    $("#spotlight_box #delete").click(function(){
        var collection_id = current_collection_id;
        var r = confirm("Are you sure?");
        if(r){
            $.ajax({
                url: "/api/collection?id="+collection_id,
                type: "delete",
                success: function(data){
                    $("#message").show()
                                 .text("You delete this post!")
                                 .delay(2000)
                                 .fadeOut();

                    window.location.href = "#";
                    load_content();
                }
            });
        }
    });

    $("#spotlight_box #comment_box #comment_post").click(function(){
        var comment = $("#spotlight_box #comment_box textarea").val();
        $.post("/api/comments?id=" + current_collection_id, {"comment":comment}, function(data){
            $("#spotlight_box #comment_box textarea").val("");
            $("#message").show()
                         .text("You comment it!")
                         .delay(2000)
                         .fadeOut();
            load_comments();
        });
    });

    /*
    var Workspace = Backbone.Router.extend({
        routes: {
            "tools/:actions": "tools",
            "*actions": "main"
        },
        main: function(actions) {
            alert(actions);
        },
        tools: function() {
            alert("tools");
        },
        search: function(query, page) {
        }
    });

    var workspace = new Workspace();

    Backbone.history.start();
    */

    if(window.location.pathname=="/tools"){
        $("#rabb8it").click(function(){
            $("#message").show()
                         .text("Drag me to your bookmarks bar")
                         .delay(2000)
                         .fadeOut();

            return false;
        });
    }else if(window.location.pathname=="/rabb8it"){
        $("#get").click();
    }else{
        $(window).resize(reload_by_width);
        load_content();

        if(!current_city && current_user_id){
            $.getJSON("/api/city", function(data){
                if(supported_cities.indexOf(data["guess_city"]) > -1){
                    // display city selection
                    if(confirm("Are you from "+data["guess_city"]+"?")){
                        $.post("/api/city", {"city": data["guess_city"]}, function(){});
                    }
                }
            });
        }

        $(window).bind('hashchange', function() {
            var id=getHash();
            if(!id){
                $("#overlay").click();
            }else if(id in collection_set){
                $("#collection"+id).click();
            }else{
                $.getJSON("/api/collection?id="+id, function(data){
                    show_content(data);
                });
            }
        });

        $(window).endlessScroll({
            fireOnce: true,
            fireDelay: true,
            loader: "<div class='loading'>LOADING...<div>",
            callback: function(p){
                load_content_more();
            }
        });
    }
});
