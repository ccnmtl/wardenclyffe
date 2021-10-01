$(document).ready(
    function() {

        var Operation = Backbone.Model.extend({
            defaults: {
            },
            initialize: function() {
                this.set({clean_status: cleanStatus(this.get('status'))});
                this.on('change:status', function() {
                    this.set({clean_status: cleanStatus(this.get('status'))});
                });
            }
        });

        var Operations = Backbone.Collection.extend({
            model: Operation,
            url: '/foo', // have to set a URL or it complains
            addOrUpdateOperation: function(o) {
                var op = this.get(o.id);
                if (op !== undefined) {
                    op.set(o);
                } else {
                    this.add(o);
                }
            }
        });

        Backbone.sync = function(method, model, options) {
            // dummy this out since we never actually
            // want to sync back to the server
        };

        var AllOperations = new Operations();

        var OperationView = Backbone.View.extend({
            tagName: 'tr',
            template: _.template($('#operation-template').html()),
            events: {},
            initialize: function() {
                _.bindAll(this, 'render');
                this.model.on('change', this.render);
                this.model.on('destroy', this.remove);
            },
            render: function() {
                this.$el.html(this.template(this.model.toJSON()));
                return this;
            }
        });

        var AppView = Backbone.View.extend({
            el: $('#bb-operations'),
            initialize: function() {
                AllOperations.bind('add', this.addOne, this);
                AllOperations.bind('reset', this.addAll, this);
                AllOperations.bind('all', this.render, this);
                // AllOperations.fetch();
            },
            addOne: function(operation) {
                var view = new OperationView({model: operation});
                var e = view.render().el;
                this.$el.prepend(e);
            },
            addAll: function() {
                AllOperations.each(this.addOne);
            },
            render: function() {
            }
        });

        new AppView();

        function getQueryParams() {
            var vars = {};
            var hash;
            var hashes = window.location.href
                .slice(window.location.href.indexOf('?') + 1).split('&');
            for (var i = 0; i < hashes.length; i++) {
                hash = hashes[i].split('=');
                vars[hash[0]] = hash[1];
            }
            return vars;
        }

        var cleanStatus = function(s) {
            return s.replace(' ', '');
        };

        var orderTableByDate = function() {
            // jquery.tablesorter is responsible for table sorting
            // just tell it it needs to update
            $('#operations').trigger('update');
        };

        var stripeTable = function() {
            $('.even').removeClass('even');
            $('.odd').removeClass('odd');
            $('#bb-operations tr:odd').addClass('odd');
            $('#bb-operations tr:even').addClass('even');
        };

        var maxRows = 200;

        var trimTable = function(maxRows) {
            // todo: just trim AllOperations to maxRows
        };

        var sortInitialized = 0;
        var mostRecentOperation = '';

        var defaultRefresh = 10000; // 10 seconds
        var maxRefresh = 1000 * 5 * 60; // 5 minutes
        var currentRefresh = defaultRefresh;

        var WCRefresh = function(e) {
            // first, we check if there are new operations at all
            // by calling /num_operations/ and comparing.
            $.ajax({
                url: '/most_recent_operation/',
                type: 'get',
                dateType: 'json',
                error: requestFailed,
                success: getMostRecentSuccess
            });
        };

        var getMostRecentSuccess = function(d) {
            if (!d) {
                requestFailed();
                return;
            }
            if (d.modified !== mostRecentOperation) {
                mostRecentOperation = d.modified;
                var data = getQueryParams();
                refreshOperations(data);
            }
            currentRefresh = defaultRefresh;
            setTimeout(WCRefresh, defaultRefresh);
        };

        var requestFailed = function() {
            // ease up on the server when it's having trouble
            currentRefresh = 2 * currentRefresh; // double the refresh time
            if (currentRefresh > maxRefresh) {
                currentRefresh = maxRefresh;
            }
            setTimeout(WCRefresh, currentRefresh);
        };

        var refreshOperationsSuccess = function(d) {
            if (!d) {
                requestFailed();
                return;
            }
            if (d.operations.length) {
                _.each(d.operations, AllOperations.addOrUpdateOperation,
                    AllOperations);
                if (sortInitialized === 0) {
                    $('#operations').tablesorter({sortList: [[4, 1]]});
                    sortInitialized = 1;
                }
                orderTableByDate();
                stripeTable();
                trimTable(maxRows);
            }
        };

        var refreshOperations = function(data) {
            $.ajax({
                url: '/recent_operations/',
                type: 'get',
                dataType: 'json',
                data: data,
                error: requestFailed,
                success: refreshOperationsSuccess
            });
        };

        jQuery(function($) {
            $(document).ready(
                function() {
                    WCRefresh();
                }
            );
        });
    });
