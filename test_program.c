#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 300

int main()
{
    int i, j, k;
    int A[N][N], B[N][N], C[N][N];

    // Initialize matrices
    for (i = 0; i < N; i++)
        for (j = 0; j < N; j++)
        {
            A[i][j] = i + j;
            B[i][j] = i - j;
            C[i][j] = 0;
        }

    // Start timing
    clock_t start = clock();

    // Matrix multiplication
    for (i = 0; i < N; i++)
        for (j = 0; j < N; j++)
            for (k = 0; k < N; k++)
                C[i][j] += A[i][k] * B[k][j];

    // End timing
    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;

    printf("C[100][100] = %d\n", C[100][100]);
    printf("Execution Time: %f seconds\n", time_spent);

    return 0;
}
