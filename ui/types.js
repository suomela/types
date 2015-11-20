"use strict";

//// Configuration

var config = {
    statcodes: ['type-word', 'type-token', 'hapax-word', 'hapax-token', 'token-word'],
    basecolor: '#337ab7',
    aspect: 0.7,
    axisoffset: 10,
    leftaxisextra: 4,
    bottomaxisextra: 2,
    triangle_threshold: 0.1,
    p_threshold: 0.1,
    fdr_threshold: 0.1,
    large_area: 400,
    small_area: 120,
    label_corner_radius: 4,
    label_x_offset: 16,
    label_y_offset: 5,
    label_x_margin: 2
};

//// Auxiliary functions

var get1 = function(a, k1) {
    return (a && k1) ? a[k1] : null;
};

var get2 = function(a, k1, k2) {
    return get1(get1(a, k1), k2);
};

var get3 = function(a, k1, k2, k3) {
    return get1(get2(a, k1, k2), k3);
};

var get4 = function(a, k1, k2, k3, k4) {
    return get1(get3(a, k1, k2, k3), k4);
};

var get0list = function(a) {
    return a ? a : [];
};

var get0obj = function(a) {
    return a ? a : {};
};

var get0first = function(a) {
    return (a && a.length) ? a[0] : null;
};

var get1list = function(a, k1) {
    return get0list(get1(a, k1));
};

var get2list = function(a, k1, k2) {
    return get0list(get2(a, k1, k2));
};

var get3list = function(a, k1, k2, k3) {
    return get0list(get3(a, k1, k2, k3));
};

var get1first = function(a, k1) {
    return get0first(get1(a, k1));
};

var get1obj = function(a, k1) {
    return get0obj(get1(a, k1));
};

var get2obj = function(a, k1, k2) {
    return get0obj(get2(a, k1, k2));
};

var set2 = function(a, k1, k2, v) {
    if (!a[k1]) {
        a[k1] = {};
    }
    a[k1][k2] = v;
};

var set3 = function(a, k1, k2, k3, v) {
    if (!a[k1]) {
        a[k1] = {};
    }
    if (!a[k1][k2]) {
        a[k1][k2] = {};
    }
    a[k1][k2][k3] = v;
};

var add1 = function(a, k, v) {
    if (!a[k]) {
        a[k] = v;
    } else {
        a[k] += v;
    }
};

var push1 = function(a, k, v) {
    if (!a[k]) {
        a[k] = [v];
    } else {
        a[k].push(v);
    }
};

var sort_numbers = function(a) {
    a.sort(function(a, b) { return a-b; });
};

var translate = function(x, y) {
    return "translate("+x+","+y+")";
};

var set_translate = function(e, x, y) {
    return e.attr("transform", translate(x, y));
};

var opt_decode = function(x) {
    if (!x || x === "n") {
        return null;
    } else {
        return x.substring(1);
    }
};

var opt_encode = function(x) {
    if (!x) {
        return "n";
    } else {
        return "p" + x;
    }
};

var compactify = function(t) {
    var compact = [];
    var cur = null;
    for (var i = 0; i < t.length; ++i) {
        var x = t[i];
        if (!Array.isArray(x)) {
            x = ["span", x];
        }
        if (!cur) {
            cur = x;
        } else if (cur[0] === x[0]) {
            cur[1] += x[1];
        } else {
            compact.push(cur);
            cur = x;
        }
    }
    if (cur) {
        compact.push(cur);
    }
    return compact;
};

var textmaker = function(e, t) {
    var compact = compactify(t);
    for (var i = 0; i < compact.length; ++i) {
        var x = compact[i];
        e.append(x[0]).text(x[1]);
    }
};

var f_large = d3.format("n");
var f_fraction = d3.format(".2r");

//// View: Plot

/*
    svg#plot
        g#curveareag                (translated)
            g#bg
            rect#cliprect
            g#clippedg              (clipped)
                g#curveg            (zoom -> translated & scaled)
                    path ...
            g#textbgareag[0]
                rect ...
            g#textbgareag[1]
                rect ...
            g#pointareag
                path ...
            g#textareag
                text ...
        g#xaxisg                    (translated)
        g#yaxisg                    (translated)
*/

var Plot = function(ctrl) {
    this.ctrl = ctrl;
    this.plotdiv = d3.select("#plot");
    this.plot = this.plotdiv.append("svg");
    this.curveareag = this.plot.append("g");
    this.bg = this.curveareag.append("rect").attr("class", "bg");
    this.cliprect = this.curveareag.append("clipPath")
        .attr("id", "plotclip").append("rect").attr("class", "bg");
    this.clippedg = this.curveareag.append("g")
        .attr("clip-path", "url(#plotclip)");
    this.textbgareag = [];
    for (var i = 0; i < 2; ++i) {
        this.textbgareag.push(this.curveareag.append("g"));
    }
    this.pointareag = this.curveareag.append("g");
    this.textareag = this.curveareag.append("g");
    this.curveg = this.clippedg.append("g");
    this.xaxisg = this.plot.append("g").attr("class", "x axis");
    this.yaxisg = this.plot.append("g").attr("class", "y axis");
    this.xscale = d3.scale.linear();
    this.yscale = d3.scale.linear();
    this.xaxis = d3.svg.axis().scale(this.xscale).orient("bottom");
    this.yaxis = d3.svg.axis().scale(this.yscale).orient("left");
    this.zoom = d3.behavior.zoom().scaleExtent([1,10]);
    this.curveareag.call(this.zoom);
    this.zoom_reset = d3.select("#zoom_reset");
    this.marginbase = 0;
    this.xticks = 0;
    this.yticks = 0;
    this.zoom_reset.on('click', this.ev_reset_zoom.bind(this));
    this.zoom.on('zoom', this.ev_zoom.bind(this));
    this.oldwidth = 0;
};

Plot.prototype.setaxis = function() {
    this.xaxisg.call(this.xaxis);
    this.yaxisg.call(this.yaxis);
};

Plot.prototype.setscale = function() {
    this.zoom.translate([0,0]).scale(1);
    this.curveg.attr("transform", null);
    this.xscale.domain([0, this.curves.maxx]);
    this.yscale.domain([0, this.curves.maxy]);
    this.zoom.x(this.xscale).y(this.yscale);
    this.setaxis();
    this.zoom_reset.style("visibility", "hidden");
};

Plot.prototype.recalc_axes = function() {
    var margin = {
        left: this.marginbase,
        right: this.marginbase,
        top: this.marginbase,
        bottom: this.marginbase
    };
    if (this.xticks) {
        margin.bottom *= config.bottomaxisextra;
    }
    if (this.yticks) {
        margin.left *= config.leftaxisextra;
    }
    var fullwidth = parseInt(this.plotdiv.style('width'));
    if (!fullwidth) {
        fullwidth = this.oldwidth;
    } else {
        this.oldwidth = fullwidth;
    }
    var fullheight = d3.round(config.aspect * fullwidth);
    var plotwidth = fullwidth - margin.left - margin.right;
    var plotheight = fullheight - margin.top - margin.bottom;
    this.plot.style('width', fullwidth + 'px');
    this.plot.style('height', fullheight + 'px');
    this.bg.attr('width', plotwidth);
    this.bg.attr('height', plotheight);
    this.cliprect.attr('x', -1);
    this.cliprect.attr('y', -1);
    this.cliprect.attr('width', plotwidth+2);
    this.cliprect.attr('height', plotheight+2);
    this.xaxis.ticks(this.xticks);
    this.yaxis.ticks(this.yticks);
    this.xaxisg.style("visibility", this.xticks ? "visible" : "hidden");
    this.yaxisg.style("visibility", this.yticks ? "visible" : "hidden");
    this.xscale.range([0, plotwidth]);
    this.yscale.range([plotheight, 0]);
    set_translate(this.xaxisg, margin.left, plotheight + margin.top + config.axisoffset);
    set_translate(this.yaxisg, margin.left - config.axisoffset, margin.top);
    set_translate(this.curveareag, margin.left, margin.top);
    this.setscale();
};

Plot.prototype.recalc_curves = function() {
    var plot = this;
    var base = d3.hsl(config.basecolor);
    var f = 0.7;
    var mid = 2;
    this.paths
        .style("fill", function(d, i) {
            if (i < mid) {
                return base.brighter(f*(mid-i));
            } else {
                return base.darker(f*(i-mid));
            }
        })
        .attr("d", function(curve) {
            var gen = d3.svg.area()
                .x(function(d) { return plot.xscale(d.x); })
                .y0(function(d) { return plot.yscale(d.y0); })
                .y1(function(d) { return plot.yscale(d.y1); });
            return gen(curve.data);
        });
};

Plot.prototype.within_bounds = function(xx, yy) {
    var x = this.xscale(xx);
    var y = this.yscale(yy);
    var x0 = this.xscale.range()[0];
    var x1 = this.xscale.range()[1];
    var y0 = this.yscale.range()[1];
    var y1 = this.yscale.range()[0];
    return x0 <= x && x <= x1 && y0 <= y && y <= y1;
};

Plot.prototype.recalc_points = function() {
    var x0 = this.xscale.range()[0];
    var x1 = this.xscale.range()[1];
    var y0 = this.yscale.range()[1];
    var y1 = this.yscale.range()[0];
    var coord = function(d) {
        var x = plot.xscale(d.x);
        var y = plot.yscale(d.y);
        var bounds = (x0 <= x && x <= x1 && y0 <= y && y <= y1);
        var vis = bounds ? "visible" : "hidden";
        return {x: x, y: y, vis: vis};
    };
    var plot = this;
    this.marks.each(function(d) {
        var c = coord(d);
        var sym;
        d3.select(this)
            .attr("transform", translate(c.x, c.y))
            .attr("d", d3.svg.symbol().size(d.area).type(d.sym))
            .style("visibility", c.vis);
    });
    this.texts.each(function(d) {
        var c = coord(d);
        d3.select(this)
            .attr("x", c.x + config.label_x_offset)
            .attr("y", c.y + config.label_y_offset)
            .text(d.collectioncode)
            .style("visibility", c.vis);
    });
    for (var j = 0; j < 2; ++j) {
        this.textbgs[j].each(function(d,i) {
            var c = coord(d);
            var bbox = plot.texts[0][i].getBBox();
            d3.select(this)
                .attr("x", bbox.x - config.label_x_margin)
                .attr("y", bbox.y)
                .attr("width", bbox.width + 2 * config.label_x_margin)
                .attr("height", bbox.height)
                .style("visibility", c.vis);
        });
    }
};

Plot.prototype.recalc_plot = function() {
    this.recalc_axes();
    this.recalc_curves();
    this.recalc_points();
};

Plot.prototype.set_curves = function(curves) {
    // needs recalc
    this.curves = curves;
    this.paths = this.curveg.selectAll("path").data(this.curves.data);
    this.paths.exit().remove();
    this.paths.enter().append("path")
        .attr("class", "curve")
        .attr("vector-effect", "non-scaling-stroke");
};

Plot.prototype.set_points = function(points) {
    // needs recalc
    for (var i = 0; i < points.length; ++i) {
        var d = points[i];
        if (d.above < config.triangle_threshold) {
            d.sym = "triangle-up";
        } else if (d.below < config.triangle_threshold) {
            d.sym = "triangle-down";
        } else {
            d.sym = "square";
        }
        d.area = (d.sel ? config.large_area : config.small_area);
    }
    var ctrl = this.ctrl;
    this.points = points;
    this.marks = this.pointareag.selectAll("path").data(this.points);
    this.marks.exit().remove();
    this.marks.enter().append("path")
        .attr("class", "point")
        .on("click", ctrl.ev_point_click.bind(ctrl));
    this.texts = this.textareag.selectAll("text").data(this.points);
    this.texts.exit().remove();
    this.texts.enter().append("text")
        .attr("class", "pointlabel")
        .on("click", ctrl.ev_point_click.bind(ctrl));
    this.textbgs = [null, null];
    for (var j = 0; j < 2; ++j) {
        this.textbgs[j] = this.textbgareag[j].selectAll("rect").data(this.points);
        this.textbgs[j].exit().remove();
        this.textbgs[j].enter().append("rect")
            .attr("class", j ? "pointlabelbg2" : "pointlabelbg1")
            .attr("rx", config.label_corner_radius)
            .attr("ry", config.label_corner_radius)
            .on("click", ctrl.ev_point_click.bind(ctrl));
    }
};

Plot.prototype.ev_zoom = function() {
    this.curveg.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
    this.setaxis();
    this.recalc_points();
    this.zoom_reset.style("visibility", "visible");
};

Plot.prototype.ev_reset_zoom = function() {
    d3.event.preventDefault();
    d3.event.stopPropagation();
    this.setscale();
    this.recalc_points();
};

//// View: Indicator

var Indicator = function() {
    this.loading = d3.select("#indicator_loading");
    this.error = d3.select("#indicator_error");
    this.msg_title = d3.select("#indicator_msg_title");
    this.msg = d3.select("#indicator_msg");
    this.info = d3.select("#info");
    this.plot_title = d3.select("#plot_title");
};

Indicator.prototype.set_loading = function(f) {
    this.loading.style("display", f ? null : "none");
};

Indicator.prototype.set_error = function(title, error) {
    this.error.style("display", null);
    this.msg_title.text(title + ":");
    this.msg.text(error);
};

Indicator.prototype.set_info = function(model) {
    this.info.selectAll("*").remove();
    var stat = model.get_stat();
    var corpus = model.get_corpus();
    var dataset = model.get_dataset();
    var p = model.get_point();
    if (stat) {
        this.plot_title.text(stat.label);
    }
    var par;
    var t;
    if (p) {
        par = this.info.append("p");
        t = [];
        t.push("This collection contains ");
        t.push(f_large(p.x) + " " + stat.xlabel);
        t.push(" and ");
        t.push(f_large(p.y) + " " + stat.ylabel);
        t.push(".");
        if (p.fraction <= config.p_threshold) {
            t.push(" Only approx. ");
        } else {
            t.push(" Approx. ");
        }
        t.push(["strong", f_fraction(100 * p.fraction) + "%"]);
        t.push(" of random collections with ");
        t.push(f_large(p.x) + " " + stat.xlabel);
        t.push(" contain ");
        t.push(p.side === "below" ? "at most" : "at least");
        t.push(" ");
        t.push(f_large(p.y) + " " + stat.ylabel);
        t.push(".");
        if (p.fraction > config.p_threshold) {
            t.push(" This seems to be a fairly typical collection.");
        } else {
            if (p.fdr > config.fdr_threshold) {
                t.push(" This finding is probably not interesting:");
                t.push(" the false discovery rate is larger than ");
                t.push(config.fdr_threshold);
                t.push(".");
            } else {
                t.push(" This finding is probably interesting:");
                t.push(" the false discovery rate is approx. ");
                t.push(["strong", f_fraction(p.fdr)]);
                t.push(".");
            }
        }
        textmaker(par, t);
    } else if (corpus) {
        par = this.info.append("p");
        t = [];
        t.push("This corpus contains ");
        t.push(f_large(corpus.samplecount) + " samples");
        t.push(" and ");
        t.push(f_large(corpus.wordcount) + " " + model.db.data.label.word.labeltext);
        t.push(".");
        textmaker(par, t);
        if (dataset) {
            par = this.info.append("p");
            t = [];
            t.push("This dataset contains ");
            t.push(f_large(dataset.hapaxes) + " " + model.db.data.label.hapax.labeltext);
            t.push(", ");
            t.push(f_large(dataset.tokens) + " " + model.db.data.label.type.labeltext);
            t.push(", and ");
            t.push(f_large(dataset.types) + " " + model.db.data.label.token.labeltext);
            t.push(".");
            textmaker(par, t);
        }
    }
};

//// View

var View = function(ctrl) {
    this.ctrl = ctrl;
    this.plot = new Plot(ctrl);
    this.indicator = new Indicator();
    this.result_table = d3.select("#result_table");
    this.sample_table = d3.select("#sample_table");
    this.context_table = d3.select("#context_table");
};

View.prototype.set_sel = function(model) {
    if (this.result_rows) {
        this.result_rows.classed("info", function(d) {
            return model.sel.corpuscode === d.corpuscode &&
                model.sel.datasetcode === d.datasetcode &&
                model.sel.collectioncode === d.collectioncode &&
                model.sel.statcode === d.statcode;
        });
    }
    if (this.sample_rows) {
        this.sample_rows.classed("info", function(d) {
            return model.sel.corpuscode === d.corpuscode &&
                model.sel.samplecode === d.samplecode;
        });
    }
};

var btn_down = '<span class="glyphicon glyphicon-sort-by-attributes"></span> ';
var btn_up = '<span class="glyphicon glyphicon-sort-by-attributes-alt"></span> ';

var td_builder = function(d) {
    var kind = d.column.kind;
    var val = kind === 'pad' ? null : d.column.val(d.row);
    var e;
    if (!val) {
        e = document.createTextNode('');
    } else if (kind == 'link') {
        e = document.createElement('a');
        e.appendChild(document.createTextNode('link'));
        e.setAttribute('href', val);
    } else if (kind == 'wrap') {
        e = document.createElement('span');
        e.appendChild(document.createTextNode(val));
    } else {
        e = document.createTextNode(val);
    }
    return e;
};

var table_builder = function(columns, data, table, row_hook) {
    table.selectAll("*").remove();
    var head = table.append("thead");
    var body = table.append("tbody");
    var tr = body.selectAll("tr")
        .data(data).enter()
        .append("tr");
    if (row_hook) {
        tr.attr("role", "button");
    }
    var td = tr.selectAll("td")
        .data(function(row, i) {
            return columns.map(function(c) {
                return { row: row, column: c };
            });
        }).enter().append("td");
    if (row_hook) {
        td.on("click", row_hook);
    }
    td.append(td_builder);
    td.attr("class", function(d) { return d.column.classed; });
    td.classed("right", function(d) { return d.column.right; });
    var sorter = function(c, i) {
        if (!c.key) {
            return;
        }
        tr.sort(function(a, b) {
            return d3.ascending(c.key(a), c.key(b));
        });
        th.classed("active", function(c2, i2) {
            return i == i2;
        });
    };
    var th = head.append("tr").selectAll("th")
        .data(columns).enter()
        .append("th")
        .attr("role", "button")
        .on("click", sorter);
    th.html(function(d) { return d.html; });
    th.classed("right", function(d) { return d.right; });
    return tr;
};

View.prototype.set_samples = function(model) {
    var columns = [
        {
            html: btn_down + 'sample',
            kind: 'plain',
            val: function(p) { return p.samplecode; },
            key: function(p) { return p.samplecode; },
        },
        {
            html: btn_down + 'description',
            kind: 'plain',
            val: function(p) { return p.description; },
            key: function(p) { return p.description; },
        },
        {
            html: btn_up + model.db.data.label.word.labeltext,
            kind: 'plain',
            val: function(p) { return f_large(p.wordcount); },
            key: function(p) { return -p.wordcount; },
            right: true,
        },
        {
            html: btn_up + model.db.data.label.token.labeltext,
            kind: 'plain',
            val: function(p) { return f_large(p.tokens); },
            key: function(p) { return -p.tokens; },
            right: true,
        },
        {
            html: btn_up + "/1000",
            kind: 'plain',
            val: function(p) { return f_fraction(p.tokens/p.wordcount*1000); },
            key: function(p) { return -p.tokens/p.wordcount; },
            right: true,
        },
        {
            html: btn_up + model.db.data.label.type.labeltext,
            kind: 'plain',
            val: function(p) { return f_large(p.types); },
            key: function(p) { return -p.types; },
            right: true,
        },
        {
            html: btn_up + model.db.data.label.hapax.labeltext,
            kind: 'plain',
            val: function(p) { return f_large(p.hapaxes); },
            key: function(p) { return -p.hapaxes; },
            right: true,
        },
        { kind: 'pad' },
        {
            html: btn_up + "unique",
            kind: 'plain',
            val: function(p) { return p.unique.join(" "); },
            key: function(p) { return -p.unique.length; },
            classed: 'wrap small',
        },
        {
            html: 'link',
            kind: 'link',
            val: function(p) { return p.link; },
        },
    ];

    this.sample_rows = table_builder(
        columns,
        model.get_samples(),
        this.sample_table,
        this.ctrl.ev_sample_cell_click.bind(this.ctrl)
    );
    this.set_sel(model);
};

View.prototype.set_context = function(model) {
    var columns = [
        {
            html: btn_down + 'sample',
            kind: 'plain',
            val: function(p) { return p.samplecode; },
            key: function(p) { return p.samplecode; },
        },
        {
            html: btn_down + 'token',
            kind: 'plain',
            val: function(p) { return p.shortlabel; },
            key: function(p) { return p.shortlabel; },
        },
        { kind: 'pad' },
        {
            html: btn_down + 'before',
            kind: 'wrap',
            val: function(p) { return p.before; },
            key: function(p) { return p.before_sort; },
            classed: 'before',
        },
        { kind: 'pad' },
        {
            html: btn_down + 'word',
            kind: 'plain',
            val: function(p) { return p.word; },
            key: function(p) { return p.word_sort; },
            classed: 'word',
        },
        { kind: 'pad' },
        {
            html: btn_down + 'after',
            kind: 'wrapwrap',
            val: function(p) { return p.after; },
            key: function(p) { return p.after_sort; },
            classed: 'after',
        },
        { kind: 'pad' },
        {
            html: 'link',
            kind: 'link',
            val: function(p) { return p.link; },
        },
    ];

    this.context_rows = table_builder(
        columns, 
        model.get_context(),
        this.context_table,
        null
    );
};

View.prototype.update_results = function(model) {
    var ctrl = this.ctrl;
    var db = model.db;
    var table = this.result_table;
    table.selectAll("*").remove();

    var columns = [
        ['corpus', function(p) { return p.corpuscode; }],
        ['dataset', function(p) { return p.datasetcode; }],
        ['collection', function(p) { return p.collectioncode; }],
        ['axes', function(p) { return db.statcode_map[p.statcode].label; }],
        ['side', function(p) { return p.side; }],
        ['p-value', function(p) {
            return f_fraction(p.fraction);
        }],
        ['FDR', function(p) {
            if (p.fdr < 1) {
                return f_fraction(p.fdr);
            } else {
                return "> 1";
            }
        }],
    ];

    var head = table.append("thead");
    head.append("tr").selectAll("th")
        .data(columns).enter()
        .append("th").text(function(d) {
            return d[0];
        });
    var body = table.append("tbody");
    this.result_rows = body.selectAll("tr")
        .data(db.point_ordered).enter()
        .append("tr")
        .attr("role", "button");
    this.result_rows.selectAll("td")
        .data(function(row, i) {
            return columns.map(function(c) {
                return { row: row, column: c };
            });
        }).enter()
        .append("td").text(function(d) {
            return d.column[1](d.row);
        })
        .on("click", ctrl.ev_result_cell_click.bind(ctrl));
    this.set_sel(model);
};

View.prototype.ev_resize = function() {
    this.plot.recalc_plot();
};

//// Controller: Input

var Input = function(ctrl) {
    this.inputs = ['corpuscode', 'datasetcode', 'groupcode', 'collectioncode', 'statcode'];
    for (var i = 0; i < this.inputs.length; ++i) {
        var l = this.inputs[i];
        this[l] = d3.select("#input_" + l);
        this[l].on({
            'change': ctrl.ev_input_changed.bind(ctrl),
            'input': ctrl.ev_input_changed.bind(ctrl)
        });
    }
};

Input.prototype.get_options = function() {
    var x = {};
    for (var i = 0; i < this.inputs.length; ++i) {
        var l = this.inputs[i];
        x[l] = opt_decode(this[l].property("value"));
    }
    return x;
};

//// Controller: Settings

var Settings = function(ctrl) {
    this.xticks = d3.select("#settings_xticks");
    this.yticks = d3.select("#settings_yticks");
    this.margin = d3.select("#settings_margin");
    this.reset = d3.select("#settings_reset");
    this.inputs = [this.xticks, this.yticks, this.margin];
    for (var i = 0; i < this.inputs.length; ++i) {
        this.inputs[i].on({
            'change': ctrl.ev_settings_changed.bind(ctrl),
            'input': ctrl.ev_settings_changed.bind(ctrl)
        });
    }
    this.reset.on('click', ctrl.ev_settings_reset.bind(ctrl));
};

Settings.prototype.reset_all = function() {
    for (var i = 0; i < this.inputs.length; ++i) {
        this.inputs[i].property("value", this.inputs[i].attr("value"));
    }
    this.reset.attr('disabled', 'disabled');
};

//// Controller

var Controller = function() {
    this.view = new View(this);
    this.model = new Model();
    this.settings = new Settings(this);
    this.input = new Input(this);
    var model = this.model;
    this.fields = [
        {
            key: 'corpuscode',
            get: model.get_corpuscodes.bind(model),
            set: set_option,
            invalidates: [
                'datasetcode', 'groupcode', 'collectioncode', 'samplecode', 'tokencode',
                'curves', 'points', 'selection'
            ],
        },
        {
            key: 'datasetcode',
            get: model.get_datasetcodes.bind(model),
            set: set_option,
            invalidates: [
                'tokencode',
                'curves', 'points', 'selection'
            ],
        },
        {
            key: 'groupcode',
            get: model.get_groupcodes.bind(model),
            set: set_option_hide,
            invalidates: [
                'collectioncode', 'samplecode', 'tokencode',
                'points', 'selection'
            ],
        },
        {
            key: 'collectioncode',
            get: model.get_collectioncodes.bind(model),
            set: set_option,
            invalidates: [
                'samplecode', 'tokencode',
                'points', 'selection'
            ],
        },
        {
            key: 'statcode',
            get: model.get_statcodes.bind(model),
            set: set_option_obj,
            invalidates: [
                'curves', 'points', 'selection'
            ],
        },
        {
            key: 'samplecode',
            invalidates: [
                'tokencode',
                'selection'
            ],
        },
        {
            key: 'tokencode',
            invalidates: [
                'selection'
            ],
        },
    ];
    this.refresh_settings();
    this.view.plot.set_curves({maxx: 1, maxy: 1, data: [{data: []}]});
    this.view.plot.set_points([]);
    this.view.plot.recalc_plot();
    d3.select(window).on('resize', this.view.ev_resize.bind(this.view));
};

Controller.prototype.refresh_settings = function() {
    var plot = this.view.plot;
    plot.marginbase = +this.settings.margin.property("value");
    plot.xticks = +this.settings.xticks.property("value");
    plot.yticks = +this.settings.yticks.property("value");
};

Controller.prototype.update_sel = function(changes) {
    if (changes.force || changes.invalid.curves) {
        this.view.plot.set_curves(this.model.get_curves());
        this.view.plot.recalc_axes();
        this.view.plot.recalc_curves();
    }
    if (changes.force || changes.invalid.points) {
        this.view.plot.set_points(this.model.get_points());
        this.view.plot.recalc_points();
        this.view.set_samples(this.model);
    }
    if (changes.force || changes.invalid.selection) {
        this.view.indicator.set_info(this.model);
        this.view.set_context(this.model);
        this.view.set_sel(this.model);
    }
};

var set_option = function(sel) {
    sel.attr("value", function(d) { return opt_encode(d); });
    sel.text(function(d) { return (d === null) ? "none" : d; });
};

var set_option_hide = function(sel) {
    sel.attr("value", function(d) { return opt_encode(d); });
    sel.text(function(d) { return (d === null) ? "none" : d.substring(1); });
};

var set_option_obj = function(sel) {
    sel.attr("value", function(d) { return opt_encode(d ? d.code : null); });
    sel.text(function(d) { return (d === null) ? "none" : d.label; });
};

Controller.prototype.set_sel_raw = function(old, x) {
    for (var i = 0; i < this.fields.length; ++i) {
        var f = this.fields[i];
        var k = f.key;
        if (k in x) {
            this.model.sel[k] = x[k];
        } else {
            this.model.sel[k] = old[k];
        }
    }
};

Controller.prototype.find_changed = function(old) {
    var changes = {
        changed: {},
        invalid: {},
        level: 0,
    };
    for (var i = 0; i < this.fields.length; ++i) {
        var f = this.fields[i];
        var k = f.key;
        if (this.model.sel[k] !== old[k]) {
            changes.changed[k] = true;
            if (f.level > changes.level) {
                changes.level = f.level;
            }
            for (var j = 0; j < f.invalidates.length; ++j) {
                changes.invalid[f.invalidates[j]] = true;
            }
        }
    }
    return changes;
};

Controller.prototype.update_inputs = function(changes) {
    for (var i = 0; i < this.fields.length; ++i) {
        var f = this.fields[i];
        var k = f.key;
        if (k in this.input) {
            var control = this.input[k];
            if (changes.force || changes.invalid[k]) {
                var values = f.get();
                var opt = control.selectAll("option").data(values);
                opt.exit().remove();
                f.set(opt.enter().append("option"));
                f.set(opt);
            }
            control.property("value", opt_encode(this.model.sel[k]));
        }
    }
};

Controller.prototype.recalc_sel = function(x, force) {
    var model = this.model;
    var old = model.sel;
    model.sel = {};
    this.set_sel_raw(old, x);
    model.fix_sel();
    var changes = this.find_changed(old);
    changes.force = force;
    this.update_inputs(changes);
    this.update_sel(changes);
};

Controller.prototype.data = function(data) {
    this.view.indicator.set_loading(false);
    this.model.set_data(data);
    this.view.update_results(this.model);
    this.recalc_sel({}, true);
};

Controller.prototype.ev_settings_reset = function() {
    this.settings.reset_all();
    this.refresh_settings();
    this.view.plot.recalc_plot();
};

Controller.prototype.ev_settings_changed = function() {
    this.refresh_settings();
    this.view.plot.recalc_plot();
    this.settings.reset.attr('disabled', null);
};

Controller.prototype.ev_input_changed = function() {
    this.recalc_sel(this.input.get_options());
};

Controller.prototype.ev_point_click = function(d, i) {
    if (this.model.all_set(d)) {
        this.recalc_sel({ collectioncode: null });
    } else {
        this.recalc_sel(d);
    }
};

Controller.prototype.ev_result_cell_click = function(d, i) {
    if (this.model.all_set(d.row)) {
        this.recalc_sel({ collectioncode: null });
    } else {
        this.recalc_sel(d.row);
    }
};

Controller.prototype.ev_sample_cell_click = function(d, i) {
    if (this.model.all_set(d.row)) {
        this.recalc_sel({ samplecode: null });
    } else {
        this.recalc_sel(d.row);
    }
};

//// Model: Database

var Database = function(data) {
    this.data = data;
    this.setup_group_maps();
    this.setup_corpuscodes();
    this.setup_datasetcodes();
    this.setup_statcodes();
    this.setup_results();
    this.setup_samples();
    this.setup_tokens();
    this.setup_context();
};

Database.prototype.setup_group_maps = function() {
    this.group_map = {};
    this.group_map_map = {};
    this.group_reverse_map = {};
    this.group_list = {};
    for (var corpuscode in this.data.collection) {
        this.setup_group_map(corpuscode);
    }
};

Database.prototype.setup_group_map = function(corpuscode) {
    var all = [];
    var other = [];
    var x = {};
    var collections = this.data.collection[corpuscode];
    for (var collectioncode in collections) {
        var collection = collections[collectioncode];
        if (collection.groupcode) {
            push1(x, collection.groupcode, collectioncode);
        } else {
            other.push(collectioncode);
        }
        all.push(collectioncode);
    }

    this.group_map[corpuscode] = {};
    this.group_map_map[corpuscode] = {};
    this.group_reverse_map[corpuscode] = {};
    this.group_list[corpuscode] = [];
    this.add_group(corpuscode, '1all', all);
    var normal_groups = Object.keys(x);
    normal_groups.sort();
    for (var i = 0; i < normal_groups.length; ++i) {
        var groupcode = normal_groups[i];
        this.add_group(corpuscode, '0' + groupcode, x[groupcode]);
    }
    if (other.length > 0 && other.length < all.length) {
        this.add_group(corpuscode, '1other', other);
    }
};

Database.prototype.add_group = function(corpuscode, groupcode, collections) {
    collections.sort();
    this.group_list[corpuscode].push(groupcode);
    this.group_map[corpuscode][groupcode] = collections;
    this.group_map_map[corpuscode][groupcode] = {};
    for (var i = 0; i < collections.length; ++i) {
        var collectioncode = collections[i];
        this.group_map_map[corpuscode][groupcode][collectioncode] = true;
        this.group_reverse_map[corpuscode][collectioncode] = groupcode;
    }
};

Database.prototype.setup_corpuscodes = function() {
    this.corpuscodes = Object.keys(this.data.corpus);
    this.corpuscodes.sort();
};

Database.prototype.setup_datasetcodes = function() {
    this.datasetcodes = {};
    for (var corpuscode in this.data.dataset) {
        var l = Object.keys(this.data.dataset[corpuscode]);
        l.sort();
        this.datasetcodes[corpuscode] = l;
    }
};

Database.prototype.setup_statcodes = function() {
    this.statcodes = [];
    this.statcode_map = {};
    for (var i = 0; i < config.statcodes.length; ++i) {
        var statcode = config.statcodes[i];
        if (this.data.stat[statcode]) {
            var x = this.data.stat[statcode].x;
            var y = this.data.stat[statcode].y;
            var xlabel = this.data.label[x].labeltext;
            var ylabel = this.data.label[y].labeltext;
            var stat = {
                code: statcode,
                x: x,
                y: y,
                xlabel: xlabel,
                ylabel: ylabel,
                label: ylabel + " / " + xlabel,
            };
            this.statcodes.push(stat);
            this.statcode_map[statcode] = stat;
        }
    }
};

Database.prototype.setup_results = function() {
    var indexes = [];
    for (var i in this.data.result_q) {
        indexes.push(+i);
    }
    sort_numbers(indexes);
    var qq = null;
    this.point_ordered = [];
    for (var j = 0; j < indexes.length; ++j) {
        var r = this.data.result_q[indexes[j]];
        if (qq === null || qq < r.q) {
            qq = r.q;
        }
        var p = this.data.result_p[r.corpuscode][r.datasetcode][r.collectioncode][r.statcode];
        if (!p.side) {
            p.fdr = qq;
            p.side = r.side;
            p.fraction = p[r.side] / p.total;
            p.corpuscode = r.corpuscode;
            p.datasetcode = r.datasetcode;
            p.collectioncode = r.collectioncode;
            p.statcode = r.statcode;
            p.groupcode = this.group_reverse_map[r.corpuscode][r.collectioncode];
            this.point_ordered.push(p);
        }
    }
    this.num_tests = indexes.length;
};

Database.prototype.setup_samples = function() {
    for (var corpuscode in this.data.sample) {
        var corpus = this.data.corpus[corpuscode];
        var samples = this.data.sample[corpuscode];
        var wc = 0;
        var sc = 0;
        for (var samplecode in samples) {
            var sample = samples[samplecode];
            sample.corpuscode = corpuscode;
            sample.samplecode = samplecode;
            wc += sample.wordcount;
            sc += 1;
        }
        corpus.wordcount = wc;
        corpus.samplecount = sc;
    }
};

Database.prototype.setup_tokens_1 = function(tokenmap, corpuscode, datasetcode) {
    for (var samplecode in this.data.sample[corpuscode]) {
        var sample = this.data.sample[corpuscode][samplecode];
        var s = {
            corpuscode: corpuscode,
            datasetcode: datasetcode,
            samplecode: samplecode,
            description: sample.description,
            wordcount: sample.wordcount,
            link: sample.link,
            tokenmap: {},
        };
        set3(this.sample_data, corpuscode, datasetcode, samplecode, s);
        var t = get3list(this.data.token, corpuscode, datasetcode, samplecode);
        for (var tokencode in t) {
            var token = t[tokencode];
            add1(tokenmap, tokencode, token.tokencount);
            add1(s.tokenmap, tokencode, token.tokencount);
        }
    }
};

Database.prototype.setup_tokens_2 = function(tokenmap, corpuscode, datasetcode) {
    for (var samplecode in this.data.sample[corpuscode]) {
        var s = this.sample_data[corpuscode][datasetcode][samplecode];
        s.unique = [];
        s.hapaxes = 0;
        s.tokens = 0;
        s.types = 0;
        for (var tokencode in s.tokenmap) {
            var gc = tokenmap[tokencode];
            var sc = s.tokenmap[tokencode];
            s.tokens += sc;
            s.types += 1;
            if (gc == 1) {
                s.hapaxes += 1;
            }
            if (gc == sc) {
                var l = get4(this.data.tokeninfo, corpuscode, datasetcode, tokencode, "shortlabel");
                if (!l) {
                    l = tokencode;
                }
                s.unique.push(l);
            }
        }
    }
};

Database.prototype.setup_tokens = function() {
    this.sample_data = {};
    for (var corpuscode in this.data.token) {
        for (var datasetcode in this.data.dataset[corpuscode]) {
            var dataset = this.data.dataset[corpuscode][datasetcode];
            var tokenmap = {};
            this.setup_tokens_1(tokenmap, corpuscode, datasetcode);
            this.setup_tokens_2(tokenmap, corpuscode, datasetcode);
            dataset.hapaxes = 0;
            dataset.tokens = 0;
            dataset.types = 0;
            for (var tokencode in tokenmap) {
                var count = tokenmap[tokencode];
                dataset.tokens += count;
                dataset.types += 1;
                if (count == 1) {
                    dataset.hapaxes += 1;
                }
            }
        }
    }
};

Database.prototype.setup_context = function() {
    for (var corpuscode in this.data.context) {
        var t1 = this.data.context[corpuscode];
        for (var datasetcode in t1) {
            var tokenmap = {};
            var t2 = t1[datasetcode];
            for (var samplecode in t2) {
                var t3 = t2[samplecode];
                for (var tokencode in t3) {
                    var t4 = t3[tokencode];
                    var tokeninfo = get3(this.data.tokeninfo, corpuscode, datasetcode, tokencode);
                    for (var i = 0; i < t4.length; ++i) {
                        var context = t4[i];
                        context.corpuscode = corpuscode;
                        context.datasetcode = datasetcode;
                        context.samplecode = samplecode;
                        context.tokencode = tokencode;
                        context.shortlabel = tokencode;
                        context.longlabel = tokencode;
                        if (tokeninfo && tokeninfo.shortlabel) {
                            context.shortlabel = tokeninfo.shortlabel;
                        }
                        if (tokeninfo && tokeninfo.longlabel) {
                            context.longlabel = tokeninfo.longlabel;
                        }
                        if (context.before) {
                            var words = context.before.split(/\s+/);
                            words.reverse();
                            context.before_sort = words.join(" ").trim().toLowerCase();
                        }
                        if (context.after) {
                            context.after_sort = context.after.trim().toLowerCase();
                        }
                        if (context.word) {
                            context.word_sort = context.word.trim().toLowerCase();
                        }
                    }
                }
            }
        }
    }
};

Database.prototype.get_curves = function(sel) {
    var curves = {
        maxx: 1,
        maxy: 1,
        data: []
    };
    var input = get3(this.data.result_curve, sel.corpuscode, sel.datasetcode, sel.statcode);
    if (!input) {
        return curves;
    }
    var levels = [];
    for (var level in input) {
        levels.push(+level);
    }
    sort_numbers(levels);
    for (var i = 0; i < levels.length; ++i) {
        this.get_one_curve(curves, input, levels[i]);
    }
    return curves;
};

Database.prototype.get_one_curve = function(curves, input, level) {
    var curve_lower = input[level].lower.id;
    var curve_upper = input[level].upper.id;
    var data_lower = this.data.result_curve_point[curve_lower];
    var data_upper = this.data.result_curve_point[curve_upper];
    var i = 0;
    var j = 0;
    var x = 0;
    var y0 = 0;
    var y1 = 0;
    var maxy = 0;
    var data = [];
    while (i < data_lower.length || j < data_upper.length) {
        var igood = false;
        var jgood = false;
        if (i == data_lower.length) {
            jgood = true;
        } else if (i == data_lower.length) {
            igood = true;
        } else {
            igood = (data_lower[i].x <= data_upper[j].x);
            jgood = (data_lower[i].x >= data_upper[j].x);
        }
        if (igood) {
            x = data_lower[i].x;
            y0 = data_lower[i].y;
            ++i;
        }
        if (jgood) {
            x = data_upper[j].x;
            y1 = data_upper[j].y;
            ++j;
        }
        data.push({x: x, y0: y0, y1: y1});
        if (y1 > maxy) {
            maxy = y1;
        }
    }
    if (x > curves.maxx) {
        curves.maxx = x;
    }
    if (maxy > curves.maxy) {
        curves.maxy = maxy;
    }
    curves.data.push({level: level, data: data});
};

Database.prototype.get_points = function(sel) {
    var points = [];
    var collections = get2list(this.group_map, sel.corpuscode, sel.groupcode);
    for (var i = 0; i < collections.length; ++i) {
        var collectioncode = collections[i];
        var input = get4(this.data.result_p, sel.corpuscode, sel.datasetcode, collectioncode, sel.statcode);
        if (input) {
            points.push({
                collectioncode: collectioncode,
                x: input.x,
                y: input.y,
                above: input.above / input.total,
                below: input.below / input.total,
                sel: (collectioncode === sel.collectioncode)
            });
        }
    }
    return points;
};

//// Model

var Model = function() {
    this.db = null;
    this.sel = {
        corpuscode: null,
        datasetcode: null,
        groupcode: null,
        collectioncode: null,
        statcode: null,
        samplecode: null,
        tokencode: null,
    };
};

Model.prototype.all_set = function(x) {
    for (var key in x) {
        if (key in this.sel && x[key] !== this.sel[key]) {
            return false;
        }
    }
    return true;
};

Model.prototype.fix_sel = function() {
    var sel = this.sel;
    var data = this.db.data;
    if (!sel.corpuscode || !(sel.corpuscode in data.corpus)) {
        sel.corpuscode = get0first(this.db.corpuscodes);
    }
    if (!sel.datasetcode || !(sel.datasetcode in get1obj(data.dataset, sel.corpuscode))) {
        sel.datasetcode = get1first(this.db.datasetcodes, sel.corpuscode);
    }
    if (!sel.groupcode || !(sel.groupcode in get1obj(this.db.group_map, sel.corpuscode))) {
        sel.groupcode = get1first(this.db.group_list, sel.corpuscode);
    }
    if (sel.collectioncode && !(sel.collectioncode in get2obj(this.db.group_map_map, sel.corpuscode, sel.groupcode))) {
        sel.collectioncode = null;
    }
    if (sel.samplecode && !(sel.samplecode in get2obj(data.sample_collection, sel.corpuscode, sel.collectioncode))) {
        sel.samplecode = null;
    }
    if (!sel.statcode || !(sel.statcode in this.db.statcode_map)) {
        sel.statcode = get1(get0first(this.db.statcodes), "code");
    }
};

Model.prototype.set_data = function(data) {
    this.db = new Database(data);
};

Model.prototype.get_curves = function() {
    return this.db.get_curves(this.sel);
};

Model.prototype.get_points = function() {
    return this.db.get_points(this.sel);
};

Model.prototype.get_corpuscodes = function() {
    return this.db.corpuscodes;
};

Model.prototype.get_datasetcodes = function() {
    return get1list(this.db.datasetcodes, this.sel.corpuscode);
};

Model.prototype.get_groupcodes = function() {
    if (!this.sel.corpuscode) {
        return [];
    }
    return this.db.group_list[this.sel.corpuscode].concat([null]);
};

Model.prototype.get_collectioncodes = function() {
    if (!this.sel.corpuscode || !this.sel.groupcode) {
        return [];
    }
    return [null].concat(this.db.group_map[this.sel.corpuscode][this.sel.groupcode]);
};

Model.prototype.get_statcodes = function() {
    return this.db.statcodes;
};

Model.prototype.get_point = function() {
    var sel = this.sel;
    return get4(this.db.data.result_p, sel.corpuscode, sel.datasetcode, sel.collectioncode, sel.statcode);
};

Model.prototype.get_stat = function() {
    var sel = this.sel;
    return get1(this.db.statcode_map, sel.statcode);
};

Model.prototype.get_corpus = function() {
    var sel = this.sel;
    return get1(this.db.data.corpus, sel.corpuscode);
};

Model.prototype.get_dataset = function() {
    var sel = this.sel;
    return get2(this.db.data.dataset, sel.corpuscode, sel.datasetcode);
};

Model.prototype.get_samples = function() {
    var sel = this.sel;
    if (sel.corpuscode && sel.datasetcode && sel.collectioncode) {
        var l = this.db.data.sample_collection[sel.corpuscode][sel.collectioncode];
        var m = this.db.sample_data[sel.corpuscode][sel.datasetcode];
        return l.map(function(samplecode) {
            return m[samplecode];
        });
    } else {
        return [];
    }
};

Model.prototype.get_context = function() {
    var sel = this.sel;
    var data = this.db.data;
    var t = get3(data.context, sel.corpuscode, sel.datasetcode, sel.samplecode);
    if (!t) {
        return [];
    } else if (sel.tokencode) {
        return get1list(t, sel.tokencode);
    } else {
        var r = [];
        for (var tokencode in t) {
            r = r.concat(get1list(t, tokencode));
        }
        return r;
    }
};


//// main

var types = new Controller();
