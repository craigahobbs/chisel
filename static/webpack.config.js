var path = require('path');
module.exports = {
    entry: {
        filename: './doc/doc.js'
    },
    output: {
        path: path.join(__dirname, '..', 'chisel', 'static', 'doc'),
        filename: 'doc.js'
    },
    module: {
        loaders: [
            {
                test: /\.js$/,
                loader: 'babel?presets[]=es2015'
            }
        ]
    }
};
