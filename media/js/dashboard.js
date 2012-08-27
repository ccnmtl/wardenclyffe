function getQueryParams() {
    var vars = {}, hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for (var i = 0; i < hashes.length; i++) {
        hash = hashes[i].split('=');
        vars[hash[0]] = hash[1];
    }
    return vars;
}

var cleanStatus = function (s) {
    return s.replace(" ", "");
};

var newRow = function (el) {
    var r = $("<tr></tr>");
    r.attr("id", "operation_" + el.id);
    r.append($("<td></td>")
             .append($("<div class=\"operation_status\"></div>").addClass(cleanStatus(el.status))));
    r.append("<td>" + el.action + "</td>");

    r.append($("<td></td>")
             .append($("<a href='" + el.video_url + "'>" + el.video_title + "</a>")));

    r.append($("<td></td>")
             .append($("<a href='" + el.collection_url + "'>" + el.collection_title + "</a>")));

    r.append("<td class=\"modified\">" + el.modified + "</td>");
    r.append("<td>" + el.video_creator + "</td>");

    return r;
};

var WCgetRow = function (operation_id) {
    var r = $("#operation_" + operation_id);
    return r;
};

var updateRow = function (oldRow, el) {
    // only fields likely to change are status and date
    var row = $("#operation_" + el.id);
    row.children(".modified").text(el.modified);
    $(".operation_status", row)
        .removeClass("complete")
        .removeClass("failed")
        .removeClass("inprogress")
        .removeClass("submitted")
        .addClass(cleanStatus(el.status));
};

var orderTableByDate = function () {
    $("#operations").trigger("update");
};

var stripeTable = function () {
    $(".even").removeClass("even");
    $(".odd").removeClass("odd");
    $("#operations tbody tr:odd").addClass("odd");
    $("#operations tbody tr:even").addClass("even");
};

var trimTable = function (maxRows) {
};

var sortInitialized = 0;
var mostRecentOperation = "";

var defaultRefresh = 10000; // 10 seconds
var maxRefresh = 1000 * 5 * 60; // 5 minutes
var currentRefresh = defaultRefresh;

var WCRefresh = function (e) {
    // first, we check if there are new operations at all
    // by calling /num_operations/ and comparing.
    $.ajax({
        url: "/most_recent_operation/",
        type: "get",
        dateType: 'json',
        error: requestFailed,
        success: function (d) {
            if (!d) {
                requestFailed();
                return;
            }
            if (d.modified === mostRecentOperation) {
                // nothing to update
            } else {
                mostRecentOperation = d.modified;
                var data = getQueryParams();
                refreshOperations(data);
            }
            currentRefresh = defaultRefresh;
            setTimeout(WCRefresh, defaultRefresh);
        }
    });
};

var requestFailed = function () {
    // ease up on the server when it's having trouble
    currentRefresh = 2 * currentRefresh; // double the refresh time
    if (currentRefresh > maxRefresh) {
        currentRefresh = maxRefresh;
    }
    setTimeout(WCRefresh, currentRefresh);
};

var refreshOperations = function (data) {
		$.ajax(
        {
            url: "/recent_operations/",
            type: 'get',
            dataType: 'json',
            data: data,
            error: requestFailed,
            success: function (d) {
                if (!d) {
                    requestFailed();
                    return;
                }
                if (d.operations.length) {
                    var rowsToAdd    = [];
                    var rowsToUpdate = [];
                    var rowsToDelete = [];
                
                    for (var i = d.operations.length - 1; i >= 0; i--) {
                        // TODO: compare/update
                        var el = d.operations[i];
                        var operation_id = el.id;
                        var oldRow = WCgetRow(operation_id);
                        if (oldRow.length > 0) {
                            rowsToUpdate.push([oldRow, el]);
                        } else {
                            rowsToAdd.push(el);
                        }
                    }
                    if (rowsToUpdate.length > 0) {
                        for (i = 0; i < rowsToUpdate.length; i++) {
                            updateRow(rowsToUpdate[i][0], rowsToUpdate[i][1]);
                        }
                    }
                    if (rowsToAdd.length > 0) {
                        for (i = 0; i < rowsToAdd.length; i++) {
                            var r = newRow(rowsToAdd[i]);
                            $("#operations tbody").prepend(r);
                        }
                    }
                    if (sortInitialized === 0) {
                        $("#operations").tablesorter({sortList: [[4, 1]]});
                        sortInitialized = 1;
                    }
                    orderTableByDate();
                    stripeTable();
                    trimTable(200);
                }
            }
        }
    );
    };


jQuery(function ($) {
    // Ensure that the CSRF token is sent with AJAX POSTs sent by jQuery
    // Taken from the documentation: http://docs.djangoproject.com/en/dev/ref/contrib/csrf/
    $('html').ajaxSend(function (event, xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        if (!(/^http:.*/.test(settings.url) || (/^https:.*/.test(settings.url)))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    });

    $(document).ready(
        function () {
            WCRefresh();
        }
    );
});
