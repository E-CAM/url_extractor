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
    s.append(".myiframebox { overflow-y: auto; }");
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

    $.when(extractor_req, featherlight_req).done(function(extract_data, featherlight_data){
        var fullurl = extract_data[0][0]['content']['URL'];

        // no preview available?
        if(fileId === confId) {
            var preview = Configuration.previewer + "/nopreview.svg";
        } else {
            var preview = Configuration.url;
        }

        $(Configuration.tab).append("<h1 align='center'><a href='" + fullurl + "' target='_blank'>" + extract_data[0][0]['content']['title'] + "</a></h1>");

        $(Configuration.tab).append("<a href='" + fullurl + "' id='mypreviewlink'><img class='fit-in-space' src='" + preview + "'/></a>");

        // lets assume if it has any value, we shouldn't iframe it.
        if(extract_data[0][0]['content'].hasOwnProperty('X-Frame-Options')) {
            $('#mypreviewlink').attr('target', '_blank');
        } else {
            $('#mypreviewlink').featherlight(fullurl, {type:'iframe', variant: 'myiframebox', loading: 'Loading ' + fullurl, iframeWidth: $(window).width() * 0.8, iframeHeight: $(window).height() * 0.8});
        }

    }).fail(function(err){
        console.log("Failed to load all scripts and data for URL previewer: " + err['status'] + " - " + err['statusText']);
    });
    
}(jQuery, Configuration));
