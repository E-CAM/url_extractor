(function ($, Configuration) {
    console.log("URL previewer for " + Configuration.id);

    var useTab = Configuration.tab;
    var referenceUrl = Configuration.url;
    var confId = Configuration.id;
    var fileId = Configuration.fileid;

    // loading featherlight
    var s = document.createElement("link");
    s.rel = "stylesheet";
    s.type = "text/css";
    s.href =  Configuration.previewer + "/featherlight/featherlight.min.css";
    $(useTab).append(s)

    s = document.createElement("style");
    s.type = "text/css";
    s.append(".featherlight-iframe .featherlight-content { overflow-y: auto; }");
    $(useTab).append(s)

    var extractor_req = $.ajax({
        type: "GET",
        url: jsRoutes.api.Files.getMetadataJsonLD(confId, "ncsa.urlextractor/1.0").url,
        // if Clowder API doesn't support above call, you can use:
        // url: "/api/files/" + confId + "/metadata.jsonld?extractor=ncsa.urlextractor/1.0",
        dataType: "json"
    });

    var featherlight_req = $.ajax({
        url: Configuration.previewer + "/featherlight/featherlight.min.js",
        dataType: "script",
        context: this,
    });

    // Create a toggle for all metadata
    toggleMetadata = function(){
        var small = "col-md-4 col-sm-4 col-lg-4"
        var medium = "col-md-8 col-sm-8 col-lg-8"
        var large = "col-md-12 col-sm-12 col-lg-12"
        // First small item is the file metadata
        var fileMetadata = document.getElementsByClassName(small)[0];
        if (fileMetadata.style.display === "none") {
            fileMetadata.style.display = "block";
            // Shrink the main div
            mainDiv = document.getElementsByClassName(large)[0];
            mainDiv.className = medium;
        } else {
            fileMetadata.style.display = "none";
            // Expand the main div
            mainDiv = document.getElementsByClassName(medium)[0];
            mainDiv.className = large;
        }
    }

    activateComments = function(){
        var tabclass = "nav nav-tabs margin-bottom-20"
        var tabs = document.getElementsByClassName(tabclass)[0].getElementsByTagName("li");
        // Make 3rd tab active
        tabs[0].classList.remove("active");
        tabs[2].classList.add("active");
        document.getElementById("tab-metadata").classList.remove("active", "in");
        document.getElementById("tab-comments").classList.add("active", "in");
    }


    $.when(extractor_req, featherlight_req).done(function(extract_data, featherlight_data){
        var fullurl = extract_data[0][0]['content']['URL'];

        // no preview available?
        if(fileId === confId) {
            var preview = Configuration.previewer + "/nopreview.svg";
        } else {
            var preview = Configuration.url;
        }

        $(Configuration.tab).append("<h4 align='center'>Please <a href='" + fullurl + "' target='_blank'>click here</a> or on image below to open content</h4>");

        $(Configuration.tab).append("<a href='" + fullurl + "' id='mypreviewlink'><img class='fit-in-space' src='" + preview + "'/></a>");

        // lets assume if it has any value, we shouldn't iframe it.
        if(extract_data[0][0]['content'].hasOwnProperty('X-Frame-Options') || (location.protocol == 'https:' && !extract_data[0][0]['content']['tls']) ) {
            $('#mypreviewlink').attr('target', '_blank');
        } else {
            if(location.protocol == 'https:'){
                fullurl = fullurl.replace(/^http:\/\//i, 'https://');
            }
            $('#mypreviewlink').featherlight(fullurl, {type:'iframe', variant: 'myiframebox', loading: 'Loading ' + fullurl, iframeWidth: $(window).width() * 0.85, iframeHeight: $(window).height() * 0.85});
        }
        // Collapse the extractor info
        $('.collapse').collapse("hide");

        $(Configuration.tab).append("<br /><br /><button onclick=\"toggleMetadata()\">Toggle metadata for this item</button>");

        // Once the page is loaded, give a default wide view and sure comments are the active tab
        window.addEventListener("DOMContentLoaded", function(){
            toggleMetadata();
            activateComments();
        });

    }).fail(function(err){
        console.log("Failed to load all scripts and data for URL previewer: " + err['status'] + " - " + err['statusText']);
    });
}(jQuery, Configuration));
