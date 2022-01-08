#include <iostream>
#include "xtensor/xarray.hpp"
#include "xtensor/xio.hpp"
#include "xtensor/xslice.hpp"
#include "xtensor/xview.hpp"
#include "ops/conv.hpp"

int main(){
    xt::xarray<double> a1
    {
    {
        {
            {2, 3},
            {3, 4},
        },
    },
    {
        {
            {2, 1},
            {3, 2},
        },
    }
    };

    // (3,1,2,2)
    xt::xarray<double> a2
    {
    {
        {
            {2, 1},
            {1, 2},
        }
    },
    {
        {
            {3, 4},
            {3, 2},
        }
    },
    {
        {
            {3, 5},
            {5, 0},
        }
    }
    };

    auto&& x = conv2d(a1, a2, 1, 1);
    std::cout << x << std::endl;
}
